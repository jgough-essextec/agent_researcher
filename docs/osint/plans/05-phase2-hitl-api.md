# Plan 05 — Phase 2 Human-in-the-Loop API

**Depends on:** Plans 01, 03, 04  
**Unlocks:** Plan 06 (Phase 3 screenshots)

---

## Goal

Wire the human-in-the-loop API endpoints that allow the user to:
1. Get the terminal commands they need to run (`GET /api/osint/jobs/{id}/commands/`)
2. Submit their terminal output (`POST /api/osint/jobs/{id}/submit-terminal-output/`)
3. Resume the LangGraph graph after terminal submission

The LangGraph workflow pauses after `generate_commands` (via `interrupt_after`). These endpoints resume it.

---

## How LangGraph Resume Works

When `interrupt_after=['generate_commands']` is set, `graph.invoke()` pauses after `generate_commands` returns. The graph's internal state is checkpointed in `MemorySaver` under the `thread_id` (= `job_id`).

To resume from the `phase2_parse` node, call:
```python
graph.invoke(
    {"terminal_submissions": [...]},  # only supply the new data
    config={"configurable": {"thread_id": str(job_id)}},
)
```
LangGraph merges the new data into the checkpointed state and continues from where it left off.

---

## TDD

### Commands Endpoint Tests

**File:** `backend/osint/tests/test_views/test_commands.py`

```python
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from osint.models import OsintJob, OsintCommandRound


@pytest.fixture
def api():
    return APIClient()


@pytest.mark.django_db
def test_get_commands_returns_round_data(api, osint_job):
    osint_job.status = 'awaiting_terminal_output'
    osint_job.save()

    OsintCommandRound.objects.create(
        osint_job=osint_job,
        round_number=1,
        commands=['whois acme.com', 'dig acme.com MX +short'],
        rationale='These commands reveal email infrastructure.',
    )

    url = reverse('osint-commands', kwargs={'pk': osint_job.id})
    response = api.get(url)

    assert response.status_code == 200
    data = response.json()
    assert 'rounds' in data
    assert len(data['rounds']) == 1
    assert len(data['rounds'][0]['commands']) == 2
    assert data['rounds'][0]['rationale'] == 'These commands reveal email infrastructure.'


@pytest.mark.django_db
def test_get_commands_rejects_wrong_status(api, osint_job):
    osint_job.status = 'phase1_research'  # not awaiting_terminal_output
    osint_job.save()

    url = reverse('osint-commands', kwargs={'pk': osint_job.id})
    response = api.get(url)

    assert response.status_code == 400


@pytest.mark.django_db
def test_get_commands_returns_404_for_unknown_job(api):
    import uuid
    url = reverse('osint-commands', kwargs={'pk': uuid.uuid4()})
    response = api.get(url)
    assert response.status_code == 404
```

### Submit Terminal Output Tests

**File:** `backend/osint/tests/test_views/test_submit_terminal.py`

```python
import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APIClient
from osint.models import OsintJob, OsintCommandRound, TerminalSubmission


@pytest.fixture
def api():
    return APIClient()


@pytest.mark.django_db
def test_submit_terminal_output_accepts_valid_payload(api, osint_job):
    osint_job.status = 'awaiting_terminal_output'
    osint_job.save()
    OsintCommandRound.objects.create(osint_job=osint_job, round_number=1, commands=[])

    payload = {
        "submissions": [
            {
                "command_type": "dig",
                "command_text": "dig acme.com MX +short",
                "output_text": "10 mail.acme.com.\n20 mail2.acme.com.",
            }
        ]
    }

    with patch('osint.views.SubmitTerminalOutputView._resume_graph'):
        url = reverse('osint-submit-terminal', kwargs={'pk': osint_job.id})
        response = api.post(url, payload, format='json')

    assert response.status_code == 202
    osint_job.refresh_from_db()
    assert osint_job.status == 'phase2_processing'


@pytest.mark.django_db
def test_submit_rejects_wrong_status(api, osint_job):
    osint_job.status = 'phase4_analysis'
    osint_job.save()

    payload = {"submissions": [{"command_type": "dig", "command_text": "", "output_text": "..."}]}
    url = reverse('osint-submit-terminal', kwargs={'pk': osint_job.id})
    response = api.post(url, payload, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_submit_rejects_empty_submissions_list(api, osint_job):
    osint_job.status = 'awaiting_terminal_output'
    osint_job.save()

    url = reverse('osint-submit-terminal', kwargs={'pk': osint_job.id})
    response = api.post(url, {"submissions": []}, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_submit_validates_output_not_executable(api, osint_job):
    """Terminal output should be accepted as-is — it's text, not executed."""
    osint_job.status = 'awaiting_terminal_output'
    osint_job.save()
    OsintCommandRound.objects.create(osint_job=osint_job, round_number=1, commands=[])

    # Even "dangerous-looking" output should be accepted as plain text
    payload = {
        "submissions": [{
            "command_type": "other",
            "command_text": "whois acme.com",
            "output_text": "; rm -rf /; echo this is just text in output",
        }]
    }

    with patch('osint.views.SubmitTerminalOutputView._resume_graph'):
        url = reverse('osint-submit-terminal', kwargs={'pk': osint_job.id})
        response = api.post(url, payload, format='json')

    assert response.status_code == 202  # accepted as text, not rejected
```

---

## Implementations

### `OsintCommandsView`

**Update `backend/osint/views.py`:**

```python
from osint.models import OsintCommandRound

class OsintCommandsView(APIView):
    def get(self, request, pk):
        try:
            job = OsintJob.objects.get(pk=pk)
        except OsintJob.DoesNotExist:
            return Response({'detail': 'Not found'}, status=http_status.HTTP_404_NOT_FOUND)

        if job.status != 'awaiting_terminal_output':
            return Response(
                {'detail': f'Commands only available in awaiting_terminal_output status. Current: {job.status}'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        rounds = OsintCommandRound.objects.filter(osint_job=job).order_by('round_number')
        return Response({
            'job_id': str(job.id),
            'organization_name': job.organization_name,
            'primary_domain': job.primary_domain,
            'rounds': [
                {
                    'round_number': r.round_number,
                    'commands': r.commands,
                    'rationale': r.rationale,
                    'output_submitted': r.output_submitted,
                }
                for r in rounds
            ],
        })
```

### `SubmitTerminalOutputView`

```python
import threading

class SubmitTerminalOutputView(APIView):
    def post(self, request, pk):
        try:
            job = OsintJob.objects.select_for_update().get(pk=pk)
        except OsintJob.DoesNotExist:
            return Response({'detail': 'Not found'}, status=http_status.HTTP_404_NOT_FOUND)

        if job.status != 'awaiting_terminal_output':
            return Response(
                {'detail': f'Expected awaiting_terminal_output, got {job.status}'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        submissions = request.data.get('submissions', [])
        if not submissions:
            return Response(
                {'detail': 'submissions must be a non-empty list'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # Mark round as submitted
        OsintCommandRound.objects.filter(
            osint_job=job, output_submitted=False
        ).update(output_submitted=True, submitted_at=timezone.now())

        # Transition to processing
        job.status = 'phase2_processing'
        job.save(update_fields=['status', 'updated_at'])

        # Resume the graph in background
        t = threading.Thread(
            target=self._resume_graph,
            args=(str(job.id), submissions),
            daemon=True,
        )
        t.start()

        serializer = OsintJobSerializer(job)
        return Response(serializer.data, status=http_status.HTTP_202_ACCEPTED)

    def _resume_graph(self, job_id: str, submissions: list) -> None:
        from osint.graph.workflow import get_graph
        graph = get_graph()
        config = {"configurable": {"thread_id": job_id}}
        graph.invoke(
            {"terminal_submissions": submissions},
            config=config,
        )
```

### `SkipScreenshotsView` and `SubmitScreenshotsView` (stubs for now)

```python
class SubmitScreenshotsView(APIView):
    def post(self, request, pk):
        # Implemented in Plan 06
        return Response({'detail': 'Not implemented yet'}, status=http_status.HTTP_501_NOT_IMPLEMENTED)


class SkipScreenshotsView(APIView):
    def post(self, request, pk):
        try:
            job = OsintJob.objects.get(pk=pk)
        except OsintJob.DoesNotExist:
            return Response({'detail': 'Not found'}, status=http_status.HTTP_404_NOT_FOUND)

        if job.status != 'awaiting_screenshots':
            return Response(
                {'detail': f'Expected awaiting_screenshots, got {job.status}'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # Resume graph with empty screenshots to skip Phase 3
        import threading
        def _resume():
            from osint.graph.workflow import get_graph
            graph = get_graph()
            config = {"configurable": {"thread_id": str(job.id)}}
            graph.invoke({"screenshots": []}, config=config)

        job.status = 'phase3_processing'
        job.save(update_fields=['status', 'updated_at'])

        t = threading.Thread(target=_resume, daemon=True)
        t.start()

        return Response({'detail': 'Screenshots skipped, analysis will proceed without them.'})
```

---

## Rate Limiting

Add to `backend/backend/settings/base.py` in `REST_FRAMEWORK` dict:

```python
'DEFAULT_THROTTLE_RATES': {
    'osint_execute': '5/hour',
    'osint_submit': '20/hour',
    ...
}
```

Add throttle class to `SubmitTerminalOutputView`:
```python
from rest_framework.throttling import ScopedRateThrottle

class SubmitTerminalOutputView(APIView):
    throttle_scope = 'osint_submit'
    ...
```

---

## Verification

```bash
cd backend
source venv/bin/activate
pytest osint/tests/test_views/ -v

# Integration flow test:
# 1. Create job
JOB=$(curl -sX POST http://localhost:8000/api/osint/jobs/ \
  -H "Content-Type: application/json" \
  -d '{"organization_name":"Test Corp","primary_domain":"testcorp.com"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 2. Execute
curl -sX POST http://localhost:8000/api/osint/jobs/$JOB/execute/

# 3. Poll until awaiting_terminal_output
curl -s http://localhost:8000/api/osint/jobs/$JOB/ | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])"

# 4. Get commands
curl -s http://localhost:8000/api/osint/jobs/$JOB/commands/ | python3 -m json.tool

# 5. Submit fake terminal output
curl -sX POST http://localhost:8000/api/osint/jobs/$JOB/submit-terminal-output/ \
  -H "Content-Type: application/json" \
  -d '{"submissions":[{"command_type":"dig","command_text":"dig testcorp.com MX +short","output_text":"10 mail.testcorp.com."}]}'

# 6. Poll until awaiting_screenshots
curl -s http://localhost:8000/api/osint/jobs/$JOB/ | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])"
```

---

## Done When

- [ ] `GET /commands/` returns 200 with rounds when status is `awaiting_terminal_output`
- [ ] `GET /commands/` returns 400 when status is wrong
- [ ] `POST /submit-terminal-output/` accepts submissions and transitions to `phase2_processing`
- [ ] `POST /submit-terminal-output/` rejects empty submissions
- [ ] Graph resumes and transitions to `awaiting_screenshots` after terminal output submitted
- [ ] `POST /skip-screenshots/` transitions job to `phase3_processing` and continues graph
- [ ] All view tests pass
