# Deep Prospecting Engine — GCP Deployment Review

**Date:** 2026-02-04
**Reviewed by:** Automated Code Review Agent
**Codebase:** `/home/jdgough/.openclaw/workspace/agent_researcher/`

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [GCP Architecture Recommendation](#2-gcp-architecture-recommendation)
3. [Bugs, Issues & Problems](#3-bugs-issues--problems)
4. [Missing Tests & Test Gaps](#4-missing-tests--test-gaps)
5. [Security Vulnerabilities](#5-security-vulnerabilities)
6. [Deployment Blocklist](#6-deployment-blocklist)
7. [Detailed Deployment Plan](#7-detailed-deployment-plan)

---

## 1. Architecture Overview

### What Is This App?

The **Deep Prospecting Engine** is an AI-powered B2B sales intelligence platform. It automates prospect research, generates use cases, creates buyer personas, and produces sales assets (one-pagers, account plans) for a company called "Pellera" (an AI/technology VAR). It uses Google Gemini as the LLM backbone and LangGraph for workflow orchestration.

### Backend Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | Django 5 + Django REST Framework | API server |
| Database | SQLite (dev) | Primary data store |
| Vector DB | ChromaDB (local) | Semantic search / memory |
| AI | Google Gemini (via `google-genai` SDK) | All LLM calls |
| Workflow | LangGraph | Research pipeline orchestration |
| PDF Export | WeasyPrint | One-pager & account plan PDFs |
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2) | Vector embeddings |

**Django Apps (6):**
- `research` — Core research jobs, reports, competitors, gap analysis + LangGraph workflow
- `ideation` — Use case generation, feasibility assessments, refined sales plays
- `assets` — Personas, one-pagers, account plans, citations, HTML/PDF export
- `projects` — Project wrapper, iterations, work products, annotations, comparison
- `memory` — ChromaDB vector store, client profiles, sales plays, memory entries
- `prompts` — Prompt template management

### Frontend Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | Next.js 14 (App Router) | React SSR/CSR |
| Language | TypeScript | Type safety |
| Styling | Tailwind CSS 3 | UI styling |
| Forms | react-hook-form | Form handling |
| Testing | Vitest + Testing Library | Unit tests |

### Communication Pattern

- **REST API** over HTTP between frontend (port 3000) and backend (port 8000)
- CORS configured for `http://localhost:3000`
- Frontend polls backend for async research job status
- No WebSocket/SSE — purely request/response with polling

### External APIs/Services

| Service | Usage | SDK |
|---------|-------|-----|
| Google Gemini API | All LLM calls (research, classification, ideation, asset generation) | `google-genai` |
| Google Gemini Deep Research | Standalone script (`src/deep_research.py`) — NOT integrated into Django | `google-genai` |

### Key Architecture Observations

1. **Async via threads, not Celery** — Background research runs in `threading.Thread`, not a task queue. This is fragile in production (thread dies = silent failure, no retry, no monitoring).
2. **SQLite** — Not suitable for production (no concurrent writes, no network access).
3. **ChromaDB local** — Uses `duckdb+parquet` local backend with deprecated settings API.
4. **No authentication** — REST Framework has `AllowAny` permission globally.
5. **No user model** — Single-tenant, no multi-user support.

---

## 2. GCP Architecture Recommendation

### Recommended Architecture

```
                        ┌─────────────────────────┐
                        │   Cloud Load Balancer    │
                        │   (HTTPS termination)    │
                        └─────────┬───────────────┘
                                  │
                    ┌─────────────┴───────────────┐
                    │                             │
           ┌────────┴────────┐          ┌─────────┴────────┐
           │  Cloud Run:     │          │  Cloud Run:       │
           │  Frontend       │          │  Backend          │
           │  (Next.js SSR)  │          │  (Django + Gunicorn)
           │  min: 0, max: 3 │          │  min: 1, max: 5   │
           └─────────────────┘          └────────┬──────────┘
                                                 │
                                    ┌────────────┴──────────────┐
                                    │                           │
                           ┌────────┴────────┐        ┌────────┴────────┐
                           │  Cloud SQL       │        │  GCS Bucket     │
                           │  (PostgreSQL 15) │        │  (ChromaDB data │
                           │  db-f1-micro     │        │  + exports)     │
                           └─────────────────┘        └─────────────────┘
                                                               │
                                                      ┌────────┴────────┐
                                                      │  Secret Manager  │
                                                      │  (API keys,     │
                                                      │   DB creds)     │
                                                      └─────────────────┘
```

### GCP Service Selection

| Component | GCP Service | Justification |
|-----------|------------|---------------|
| **Backend** | **Cloud Run** | Stateless Django app, auto-scaling, pay-per-request. Long-running research jobs (1-5 min) fit within Cloud Run's 60-min timeout. |
| **Frontend** | **Cloud Run** | Next.js SSR as a container. Could also use Firebase Hosting for static export. |
| **Database** | **Cloud SQL (PostgreSQL 15)** | Managed PostgreSQL replaces SQLite. `db-f1-micro` for dev, `db-custom-1-3840` for prod. |
| **Vector Store** | **Cloud Run sidecar / Vertex AI Vector Search** | ChromaDB can run as a sidecar or separate Cloud Run service with GCS persistence. For production scale, migrate to Vertex AI Vector Search. |
| **Secrets** | **Secret Manager** | GEMINI_API_KEY, Django SECRET_KEY, DB credentials. |
| **Storage** | **Cloud Storage (GCS)** | PDF exports, static files, ChromaDB persistence. |
| **Task Queue** | **Cloud Tasks** | Replace `threading.Thread` for research jobs. Enables retries, monitoring, and decouples request from processing. |
| **Monitoring** | **Cloud Monitoring + Cloud Logging** | Django logging → Cloud Logging. Set up alerts for failed research jobs. |
| **DNS** | **Cloud DNS** | Custom domain management. |
| **CDN** | **Cloud CDN** (optional) | Cache static frontend assets. |

### Why NOT These Alternatives

| Alternative | Why Not |
|------------|---------|
| GKE (Kubernetes) | Overkill for this app's scale. Cloud Run is simpler and cheaper. |
| App Engine | Less control over container, cold start issues with ML models. |
| Compute Engine VMs | Undifferentiated heavy lifting. Cloud Run handles scaling. |
| Firestore | App uses relational data heavily (FKs, joins). PostgreSQL is the right fit. |
| Cloud Functions | Research jobs run 1-5+ minutes — exceeds Gen1 limits, Gen2 could work but Cloud Run is better for the full Django app. |

### Network Architecture

- Frontend Cloud Run → Backend Cloud Run via **internal** URL (VPC connector not needed for Cloud Run to Cloud Run)
- Backend Cloud Run → Cloud SQL via **Cloud SQL Auth Proxy** (built into Cloud Run)
- Backend Cloud Run → Gemini API via **public internet** (outbound)
- All services in `us-central1` to minimize latency

### Estimated Monthly Costs (Low-Medium Traffic)

| Service | Spec | Estimated Cost |
|---------|------|---------------|
| Cloud Run (Backend) | 1 vCPU, 512MB, min 1 instance | ~$20-40/mo |
| Cloud Run (Frontend) | 0.5 vCPU, 256MB, min 0 instances | ~$5-15/mo |
| Cloud SQL (PostgreSQL) | db-f1-micro, 10GB SSD | ~$10-15/mo |
| Secret Manager | 5 secrets, <1000 accesses/mo | ~$0.06/mo |
| Cloud Storage | 1GB for exports/ChromaDB | ~$0.03/mo |
| Cloud Load Balancer | SSL cert, routing | ~$18/mo |
| Gemini API | Pay-per-token (external cost) | Variable ($5-100/mo) |
| **Total (excl. Gemini)** | | **~$55-90/mo** |

---

## 3. Bugs, Issues & Problems

### 🔴 Critical Issues

#### 3.1 ChromaDB Settings API is Deprecated
**File:** `backend/memory/services/vectorstore.py`
```python
self._client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory=self.persist_directory,
    anonymized_telemetry=False,
))
```
**Problem:** `chroma_db_impl` and `Settings` constructor were deprecated in ChromaDB 0.4.x. Modern versions use `chromadb.PersistentClient(path=...)`.
**Fix:** Update to `chromadb.PersistentClient(path=self.persist_directory, settings=chromadb.Settings(anonymized_telemetry=False))`

#### 3.2 Background Threads Will Not Work in Production
**File:** `backend/research/views.py`
```python
thread = threading.Thread(target=run_research_async, args=(str(job.id),))
thread.start()
```
**Problem:** In production with Gunicorn/multiple workers, threads are not managed, not retried on failure, and die silently. Worker restarts kill in-flight threads. Cloud Run may scale down instances mid-research.
**Fix:** Replace with Cloud Tasks, Celery, or Django-Q for production task queue.

#### 3.3 SQLite Cannot Handle Production Traffic
**File:** `backend/backend/settings/base.py`
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```
**Problem:** SQLite doesn't support concurrent writes, has no network access, and data is lost on container restart in Cloud Run.
**Fix:** Add PostgreSQL configuration in `prod.py`.

#### 3.4 IterationComparator References Non-Existent Related Names
**File:** `backend/projects/services/comparison.py`, lines in `_extract_iteration_data`:
```python
data['use_cases_count'] = job.use_cases.count()
data['personas_count'] = job.personas.count()
```
**Problem:** `use_cases` and `personas` are related names on `ResearchJob` from `ideation.UseCase` and `assets.Persona` models respectively. These work BUT they trigger N+1 queries. More importantly, if the comparator is called on iterations without research jobs, it will throw `AttributeError`. The `hasattr` checks only protect the outer level, not the inner `.use_cases` / `.personas` calls.

#### 3.5 WSGI Defaults to Dev Settings
**File:** `backend/backend/wsgi.py`
```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.dev')
```
**Problem:** Production WSGI will use dev settings by default (DEBUG=True, ALLOWED_HOSTS=['*']) unless explicitly overridden.
**Fix:** Change default to `backend.settings.prod` or ensure env var is always set.

### 🟡 Moderate Issues

#### 3.6 `ContextAccumulator._get_use_cases` References `job.use_cases` Directly
**File:** `backend/projects/services/context.py`
```python
use_cases = job.use_cases.filter(priority='high')[:5]
```
**Problem:** Works but assumes use cases always exist. If no use cases are generated for an iteration, this returns empty list (fine), but the access pattern assumes the `research_job` attribute always exists. The `hasattr` check only verifies `research_job` existence, not whether `use_cases` have been generated.

#### 3.7 `manage.py` Defaults to Dev Settings
**File:** `backend/manage.py`
Same issue as WSGI — defaults to dev settings.

#### 3.8 No `STATIC_ROOT` Setting for Production
**File:** `backend/backend/settings/prod.py`
**Problem:** Missing `STATIC_ROOT` for `collectstatic`. Django admin won't serve static files in production.
**Fix:** Add `STATIC_ROOT = BASE_DIR / 'staticfiles'` and configure whitenoise or GCS.

#### 3.9 Prompts Migration Missing
**File:** `backend/prompts/migrations/`
Only has `0001_initial.py` and `__init__.py`. The `PromptTemplate` model is defined but no migration file was included in the listing (though `0001_initial.py` exists).

#### 3.10 Root `requirements.txt` Mismatch
**File:** `/requirements.txt` (root)
```
google-genai>=1.0.0
python-dotenv
```
This is for the standalone `src/deep_research.py` script and doesn't include Django dependencies. The real requirements are in `backend/requirements.txt`. This could confuse deployment scripts.

#### 3.11 `IterationCreateSerializer` Missing `project` Field Handling
**File:** `backend/projects/serializers.py`
```python
class IterationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Iteration
        fields = ['id', 'project', 'name', 'sales_history', 'prompt_override']
```
**Problem:** `project` is in `fields` but the view sets it via `perform_create(serializer.save(project=project))`. If the client sends a `project` value in the POST body, it could conflict. Should be `read_only_fields = ['id', 'project']`.

#### 3.12 No Database Connection Pooling
**Problem:** Django's default database connection handling creates a new connection per request. For Cloud SQL, should use `django-db-connection-pool` or pgbouncer.

### 🟢 Minor Issues

#### 3.13 `SECURE_SSL_REDIRECT` Not Set in Production
**File:** `backend/backend/settings/prod.py`
Missing `SECURE_SSL_REDIRECT = True`, `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`.

#### 3.14 Dark Mode CSS Without Dark Mode Support
**File:** `frontend/app/globals.css`
Dark mode CSS variables defined but no dark mode implementation in Tailwind config.

#### 3.15 `silent_memory.js` is a Mermaid Diagram (Misleading Extension)
**File:** `silent_memory.js`
Contains a Mermaid graph definition, not JavaScript. Should be `silent_memory.mmd` or `.md`.

#### 3.16 `PromptEditor` Loads Prompt Twice
**File:** `frontend/components/PromptEditor.tsx` and `frontend/components/ResearchForm.tsx`
Both components call `api.getDefaultPrompt()` on mount — the parent loads it and passes via props, but the child also has a `useEffect` that loads it if `value` is empty (which it is initially).

---

## 4. Missing Tests & Test Gaps

### Existing Tests

| Location | Type | Coverage |
|----------|------|----------|
| `backend/research/tests/test_config.py` | Config validation | Settings existence checks |
| `backend/research/tests/test_views.py` | API integration | CRUD for research jobs (4 tests) |
| `backend/conftest.py` | Pytest fixtures | Basic DB setup |
| `frontend/__tests__/api.test.ts` | Unit tests | API client methods (4 tests) |
| `frontend/__tests__/ResearchForm.test.tsx` | Component tests | Form rendering & validation (4 tests) |

**Total: ~12 tests**

### What's NOT Tested (Critical Gaps)

#### Backend — Zero Tests For:

| Module | Missing Tests | Risk |
|--------|--------------|------|
| **LangGraph Workflow** | No tests for `workflow.py`, `nodes.py`, state transitions | HIGH — Core business logic untested |
| **Gemini Client** | No tests for `gemini.py` (mocked or integration) | HIGH — All LLM interactions untested |
| **Classifier Service** | No tests for `classifier.py` keyword matching or LLM classification | MEDIUM |
| **Competitor Service** | No tests for `competitor.py` | MEDIUM |
| **Gap Analysis Service** | No tests for `gap_analysis.py` | MEDIUM |
| **Use Case Generator** | No tests for `use_case_generator.py` | MEDIUM |
| **Feasibility Service** | No tests for `feasibility.py` | MEDIUM |
| **Play Refiner** | No tests for `play_refiner.py` | MEDIUM |
| **Persona Generator** | No tests for `persona.py` | MEDIUM |
| **One-Pager Generator** | No tests for `one_pager.py` | MEDIUM |
| **Account Plan Generator** | No tests for `account_plan.py` | MEDIUM |
| **Export Service** | No tests for `export.py` HTML/PDF generation | MEDIUM |
| **Memory/Vector Store** | No tests for `vectorstore.py`, `capture.py`, `context.py` | MEDIUM |
| **Context Accumulator** | No tests for `context.py` (iterative context building) | HIGH — Core feature |
| **Iteration Comparator** | No tests for `comparison.py` | LOW |
| **Projects Views** | No tests for project/iteration CRUD, start, compare | HIGH |
| **Ideation Views** | No tests for use case generation, feasibility, play endpoints | MEDIUM |
| **Assets Views** | No tests for persona, one-pager, account plan generation | MEDIUM |
| **Memory Views** | No tests for context query, capture from research | MEDIUM |
| **Prompts Views** | No tests for prompt CRUD | LOW |

#### Frontend — Zero Tests For:

| Component | Missing Tests | Risk |
|-----------|--------------|------|
| **ResearchResults** | No tests for tab rendering, data display | MEDIUM |
| **Navigation** | No tests | LOW |
| **All Project Components** | No tests for ProjectCard, ProjectHeader, IterationTabs, etc. | MEDIUM |
| **Project Pages** | No tests for project list, new project, dashboard, iterate | HIGH |
| **Polling Logic** | No tests for poll/retry behavior | MEDIUM |

### Recommended Test Priority

1. **LangGraph workflow** — Mock Gemini client, test state transitions (validate → research → classify → compete → gaps → finalize)
2. **Gemini client** — Mock HTTP responses, test JSON parsing, error handling
3. **Project iteration flow** — Create project → create iteration → start → complete
4. **Context accumulator** — Test context inheritance between iterations
5. **All service classes** — Mock Gemini, test JSON parsing/error handling

---

## 5. Security Vulnerabilities

### 🔴 Critical

#### 5.1 No Authentication or Authorization
**All endpoints are public** (`AllowAny` permission class globally).
```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}
```
**Impact:** Anyone can create research jobs (consuming Gemini API credits), read all data, delete projects, etc.
**Fix:** Implement authentication (JWT, session-based, or Google IAP in front of Cloud Run).

#### 5.2 API Key Exposure Risk
**File:** `backend/backend/settings/base.py`
```python
GEMINI_API_KEY = env('GEMINI_API_KEY', default='')
```
**Risk:** If `.env` file is accidentally committed, API key leaks. The `.gitignore` covers `.env` but no additional protections exist.
**Fix:** Use GCP Secret Manager. Never fall back to empty string — fail loudly.

#### 5.3 Default Secret Key
```python
SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-key-change-in-production')
```
**Risk:** If `SECRET_KEY` env var is not set in production, the default insecure key is used, compromising session security and CSRF.
**Fix:** Remove default value for prod. Fail on startup if not set.

### 🟡 Moderate

#### 5.4 CORS is Configurable but Defaults to Localhost
```python
CORS_ALLOWED_ORIGINS = env('CORS_ALLOWED_ORIGINS')
```
**Risk:** Low in current state, but must be properly set for production domain. No `CORS_ALLOW_ALL_ORIGINS = True` which is good.

#### 5.5 No Rate Limiting
**Risk:** Any client can spam the research endpoint, triggering unlimited Gemini API calls.
**Fix:** Add `django-ratelimit` or use Cloud Run's built-in concurrency limits + API Gateway.

#### 5.6 No Input Sanitization on LLM Prompts
**Files:** All service files that format prompts with user input
```python
prompt = self.DEEP_RESEARCH_PROMPT.format(
    client_name=state.get('client_name', ''),
    sales_history=state.get('sales_history', ''),
)
```
**Risk:** Prompt injection — malicious `client_name` or `sales_history` could manipulate LLM behavior.
**Fix:** Sanitize inputs, limit length, use structured input rather than string interpolation.

#### 5.7 No CSRF Protection for API
REST Framework's `AllowAny` bypasses CSRF. In a session-based auth setup, this would be a vulnerability. Currently N/A since there's no auth, but becomes critical when auth is added.

#### 5.8 HTML Content Injection
**File:** `backend/assets/services/export.py`
One-pager and account plan HTML templates inject content directly:
```python
html = self.ONE_PAGER_TEMPLATE.format(
    title=one_pager.title,
    ...
)
```
**Risk:** If LLM-generated content contains HTML/script tags, XSS via the HTML export endpoints.
**Fix:** Escape HTML entities in template values.

### 🟢 Low

#### 5.9 SQL Injection — LOW Risk
Django ORM is used consistently. No raw SQL queries found. Risk is minimal.

#### 5.10 Verbose Error Messages
Exception details are returned to clients in some error responses. Should return generic messages in production.

---

## 6. Deployment Blocklist

### Must Change Before Deployment

| # | Item | Priority | Effort |
|---|------|----------|--------|
| 1 | **Add authentication** | 🔴 Critical | Medium — add Google IAP or JWT auth |
| 2 | **Replace SQLite with PostgreSQL** | 🔴 Critical | Low — add to `prod.py` settings |
| 3 | **Replace threading with task queue** | 🔴 Critical | Medium — Cloud Tasks or Celery |
| 4 | **Add Dockerfiles** (both frontend & backend) | 🔴 Critical | Low |
| 5 | **Fix ChromaDB deprecated API** | 🔴 Critical | Low |
| 6 | **Set production security settings** | 🔴 Critical | Low |
| 7 | **Configure Secret Manager** for all secrets | 🟡 High | Low |
| 8 | **Add STATIC_ROOT and static file serving** | 🟡 High | Low |
| 9 | **Add rate limiting** | 🟡 High | Low |
| 10 | **Add health check endpoint** | 🟡 High | Low |
| 11 | **Update WSGI/manage.py defaults** to prod | 🟡 High | Trivial |
| 12 | **Add HTTPS redirect** and secure cookies | 🟡 High | Trivial |
| 13 | **Input sanitization** for LLM prompts | 🟡 Medium | Low |
| 14 | **HTML escaping** in export templates | 🟡 Medium | Low |

### Missing Dockerfiles

Neither `backend/` nor `frontend/` has a `Dockerfile`. These are required for Cloud Run deployment.

### Required Environment Variables (Production)

**Backend:**
| Variable | Source | Description |
|----------|--------|-------------|
| `DJANGO_SETTINGS_MODULE` | Env | `backend.settings.prod` |
| `SECRET_KEY` | Secret Manager | Django secret key |
| `GEMINI_API_KEY` | Secret Manager | Google Gemini API key |
| `DATABASE_URL` | Secret Manager | PostgreSQL connection string |
| `ALLOWED_HOSTS` | Env | Production domain(s) |
| `CORS_ALLOWED_ORIGINS` | Env | Frontend production URL |
| `CHROMA_PERSIST_DIR` | Env / GCS | ChromaDB storage path |
| `GCS_BUCKET_NAME` | Env | For PDF exports / static files |
| `PORT` | Cloud Run auto | HTTP port (default 8080) |

**Frontend:**
| Variable | Source | Description |
|----------|--------|-------------|
| `NEXT_PUBLIC_API_URL` | Env | Backend Cloud Run URL |
| `PORT` | Cloud Run auto | HTTP port (default 3000) |

### Database Migration Strategy

1. Cloud SQL PostgreSQL instance is created via Terraform/gcloud
2. Connect via Cloud SQL Auth Proxy for initial migration
3. Run `python manage.py migrate` from a Cloud Build step or Cloud Run job
4. For subsequent deployments, run migrations as a pre-deploy step in CI/CD
5. Consider `django-migration-linter` to catch dangerous migrations

---

## 7. Detailed Deployment Plan

### Phase 1: Pre-Deployment Preparation (1-2 days)

#### Step 1.1: Fix Critical Code Issues

```bash
# Fix ChromaDB client initialization
# In backend/memory/services/vectorstore.py, replace:
#   chromadb.Client(Settings(...))
# With:
#   chromadb.PersistentClient(path=self.persist_directory)

# Fix WSGI default settings
# In backend/backend/wsgi.py:
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.prod')

# Same for manage.py
```

#### Step 1.2: Add PostgreSQL Support

Add to `backend/backend/settings/prod.py`:
```python
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default='postgres://localhost/prospecting_engine',
        conn_max_age=600,
    )
}
```

Add to `backend/requirements.txt`:
```
psycopg2-binary>=2.9.0
dj-database-url>=2.0.0
gunicorn>=21.2.0
whitenoise>=6.5.0
```

#### Step 1.3: Add Production Security Settings

Update `backend/backend/settings/prod.py`:
```python
from .base import *

DEBUG = False

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

STATIC_ROOT = BASE_DIR / 'staticfiles'

# Add whitenoise to middleware (after SecurityMiddleware)
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

#### Step 1.4: Create Backend Dockerfile

Create `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=backend.settings.prod
ENV PORT=8080

WORKDIR /app

# Install system dependencies for weasyprint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE ${PORT}

CMD exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:${PORT} \
    --workers 2 \
    --threads 4 \
    --timeout 300 \
    --access-logfile - \
    --error-logfile -
```

#### Step 1.5: Create Frontend Dockerfile

Create `frontend/Dockerfile`:
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE ${PORT}
CMD ["node", "server.js"]
```

Update `frontend/next.config.mjs`:
```javascript
const nextConfig = {
  output: 'standalone',
};
export default nextConfig;
```

#### Step 1.6: Add Health Check Endpoint

Add to `backend/backend/urls.py`:
```python
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    path('health/', health_check, name='health-check'),
    ...
]
```

### Phase 2: GCP Infrastructure Setup (1 day)

#### Step 2.1: Create GCP Project and Enable APIs

```bash
# Set project
export PROJECT_ID=deep-prospecting-engine
export REGION=us-central1

# Create project (if needed)
gcloud projects create $PROJECT_ID

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    --project=$PROJECT_ID
```

#### Step 2.2: Create Artifact Registry

```bash
gcloud artifacts repositories create prospecting-engine \
    --repository-format=docker \
    --location=$REGION \
    --project=$PROJECT_ID
```

#### Step 2.3: Create Cloud SQL Instance

```bash
# Create PostgreSQL instance
gcloud sql instances create prospecting-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --storage-size=10GB \
    --storage-type=SSD \
    --project=$PROJECT_ID

# Create database
gcloud sql databases create prospecting_engine \
    --instance=prospecting-db \
    --project=$PROJECT_ID

# Create user
gcloud sql users create appuser \
    --instance=prospecting-db \
    --password=GENERATE_STRONG_PASSWORD \
    --project=$PROJECT_ID
```

#### Step 2.4: Configure Secret Manager

```bash
# Create secrets
echo -n "your-django-secret-key-$(openssl rand -hex 32)" | \
    gcloud secrets create django-secret-key --data-file=- --project=$PROJECT_ID

echo -n "your-gemini-api-key" | \
    gcloud secrets create gemini-api-key --data-file=- --project=$PROJECT_ID

echo -n "postgres://appuser:PASSWORD@/prospecting_engine?host=/cloudsql/$PROJECT_ID:$REGION:prospecting-db" | \
    gcloud secrets create database-url --data-file=- --project=$PROJECT_ID
```

#### Step 2.5: Grant Permissions

```bash
# Get Cloud Run service account
export SA_EMAIL=$(gcloud iam service-accounts list \
    --filter="email:compute@developer.gserviceaccount.com" \
    --format="value(email)" \
    --project=$PROJECT_ID)

# Grant Secret Manager access
gcloud secrets add-iam-policy-binding django-secret-key \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID

gcloud secrets add-iam-policy-binding gemini-api-key \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID

gcloud secrets add-iam-policy-binding database-url \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID

# Grant Cloud SQL access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/cloudsql.client"
```

### Phase 3: Build & Deploy (1 day)

#### Step 3.1: Build and Push Backend Image

```bash
cd backend

# Build
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/prospecting-engine/backend:latest .

# Push
docker push $REGION-docker.pkg.dev/$PROJECT_ID/prospecting-engine/backend:latest
```

#### Step 3.2: Run Database Migrations

```bash
# Deploy a one-off Cloud Run job for migrations
gcloud run jobs create migrate-db \
    --image=$REGION-docker.pkg.dev/$PROJECT_ID/prospecting-engine/backend:latest \
    --set-secrets=SECRET_KEY=django-secret-key:latest,GEMINI_API_KEY=gemini-api-key:latest,DATABASE_URL=database-url:latest \
    --set-cloudsql-instances=$PROJECT_ID:$REGION:prospecting-db \
    --set-env-vars=DJANGO_SETTINGS_MODULE=backend.settings.prod \
    --command=python,manage.py,migrate \
    --region=$REGION \
    --project=$PROJECT_ID

# Execute migration job
gcloud run jobs execute migrate-db --region=$REGION --project=$PROJECT_ID
```

#### Step 3.3: Deploy Backend to Cloud Run

```bash
gcloud run deploy backend \
    --image=$REGION-docker.pkg.dev/$PROJECT_ID/prospecting-engine/backend:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --set-secrets=SECRET_KEY=django-secret-key:latest,GEMINI_API_KEY=gemini-api-key:latest,DATABASE_URL=database-url:latest \
    --set-cloudsql-instances=$PROJECT_ID:$REGION:prospecting-db \
    --set-env-vars=DJANGO_SETTINGS_MODULE=backend.settings.prod,ALLOWED_HOSTS=backend-HASH-uc.a.run.app \
    --min-instances=1 \
    --max-instances=5 \
    --memory=512Mi \
    --cpu=1 \
    --timeout=300 \
    --concurrency=80 \
    --project=$PROJECT_ID
```

#### Step 3.4: Get Backend URL and Deploy Frontend

```bash
# Get backend URL
export BACKEND_URL=$(gcloud run services describe backend --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)

# Build frontend with backend URL
cd ../frontend
docker build \
    --build-arg NEXT_PUBLIC_API_URL=$BACKEND_URL \
    -t $REGION-docker.pkg.dev/$PROJECT_ID/prospecting-engine/frontend:latest .

docker push $REGION-docker.pkg.dev/$PROJECT_ID/prospecting-engine/frontend:latest

# Deploy frontend
gcloud run deploy frontend \
    --image=$REGION-docker.pkg.dev/$PROJECT_ID/prospecting-engine/frontend:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --min-instances=0 \
    --max-instances=3 \
    --memory=256Mi \
    --cpu=1 \
    --timeout=60 \
    --project=$PROJECT_ID
```

#### Step 3.5: Update Backend CORS

```bash
export FRONTEND_URL=$(gcloud run services describe frontend --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)

# Update backend with correct CORS origin
gcloud run services update backend \
    --update-env-vars=CORS_ALLOWED_ORIGINS=$FRONTEND_URL \
    --region=$REGION \
    --project=$PROJECT_ID
```

### Phase 4: DNS & Domain Setup (Optional)

```bash
# Map custom domain
gcloud run domain-mappings create \
    --service=frontend \
    --domain=prospecting.yourdomain.com \
    --region=$REGION \
    --project=$PROJECT_ID

gcloud run domain-mappings create \
    --service=backend \
    --domain=api.prospecting.yourdomain.com \
    --region=$REGION \
    --project=$PROJECT_ID

# Follow DNS verification instructions output by the commands above
```

### Phase 5: Post-Deploy Verification

#### Step 5.1: Health Checks

```bash
# Backend health
curl -s $BACKEND_URL/health/ | jq .
# Expected: {"status": "ok"}

# Backend API
curl -s $BACKEND_URL/api/prompts/default/ | jq .
# Expected: JSON with default prompt

# Frontend
curl -s -o /dev/null -w "%{http_code}" $FRONTEND_URL
# Expected: 200
```

#### Step 5.2: Functional Smoke Test

```bash
# Create a research job
curl -X POST $BACKEND_URL/api/research/ \
    -H "Content-Type: application/json" \
    -d '{"client_name": "Google", "sales_history": "Test"}' | jq .

# Check the returned job ID and poll for completion
JOB_ID=<returned-id>
curl -s $BACKEND_URL/api/research/$JOB_ID/ | jq .status
```

#### Step 5.3: Create a Project End-to-End

```bash
# Create project
curl -X POST $BACKEND_URL/api/projects/ \
    -H "Content-Type: application/json" \
    -d '{"name": "Smoke Test", "client_name": "Acme Corp", "context_mode": "accumulate"}' | jq .

# Create and start iteration (via frontend for full test)
```

#### Step 5.4: Monitoring Setup

```bash
# Set up uptime check
gcloud monitoring uptime create \
    --display-name="Backend Health" \
    --resource-type=uptime-url \
    --hostname=$(echo $BACKEND_URL | sed 's|https://||') \
    --path=/health/ \
    --check-frequency=5m \
    --project=$PROJECT_ID
```

#### Step 5.5: Verify Logs

```bash
# Check for errors in Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
    --limit=20 \
    --project=$PROJECT_ID
```

---

## Summary

### Deployment Readiness: 🟡 MODERATE — Needs Work

**The app is well-structured and functional for local development.** The Django+Next.js architecture is clean, the LangGraph workflow is well-designed, and the data model is comprehensive. However, several changes are required before production deployment:

| Category | Status |
|----------|--------|
| Architecture | ✅ Clean separation, good module design |
| Database | ❌ SQLite → needs PostgreSQL |
| Task Queue | ❌ Threads → needs Cloud Tasks/Celery |
| Authentication | ❌ None → needs at minimum Google IAP |
| Dockerfiles | ❌ Missing |
| Security | 🟡 Default secret key, no rate limiting |
| Tests | ❌ Minimal (12 tests, core logic untested) |
| Production Settings | 🟡 Incomplete prod.py |
| Vector Store | 🟡 Deprecated ChromaDB API |
| CI/CD | ❌ None configured |

**Estimated time to production-ready:** 3-5 developer days for critical items, 1-2 additional weeks for comprehensive testing and hardening.
