from osint.graph.state import OsintState
from osint.models import OsintJob, TerminalSubmission
from osint.services.terminal_parser import parse_terminal_output


def phase2_parse_terminal(state: OsintState) -> OsintState:
    """Phase 2: Parse user-submitted terminal output via Gemini."""
    submissions = state.get('terminal_submissions') or []

    if not submissions:
        OsintJob.objects.filter(pk=state['job_id']).update(status='awaiting_screenshots')
        return {**state, 'status': 'awaiting_screenshots'}

    all_parsed = []
    for submission in submissions:
        parsed = parse_terminal_output(
            raw_output=submission.get('output_text', ''),
            command_type=submission.get('command_type', 'other'),
        )
        TerminalSubmission.objects.create(
            osint_job_id=state['job_id'],
            command_type=submission.get('command_type', 'other'),
            command_text=submission.get('command_text', ''),
            output_text=submission.get('output_text', ''),
            parsed_data={
                'records': [
                    {'type': r.type, 'name': r.name, 'value': r.value, 'analysis': r.analysis}
                    for r in parsed.records
                ],
                'key_observations': list(parsed.key_observations),
                'technology_signals': list(parsed.technology_signals),
            },
        )
        all_parsed.append({
            'records': [{'type': r.type, 'name': r.name, 'value': r.value} for r in parsed.records],
            'technology_signals': list(parsed.technology_signals),
        })

    OsintJob.objects.filter(pk=state['job_id']).update(status='awaiting_screenshots')

    return {
        **state,
        'status': 'awaiting_screenshots',
        'terminal_submissions': all_parsed,
    }
