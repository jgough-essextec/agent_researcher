# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Deep Prospecting Engine — an AI-powered sales research tool. Django 5 + DRF backend, Next.js 14 frontend, Google Gemini for AI, LangGraph for workflow orchestration.

## Commands

### Backend (run from `backend/`)

```bash
# Activate venv
source venv/bin/activate

# Run dev server
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Tests
pytest
pytest research/tests/test_views.py  # single test file
pytest -k "test_name"                # single test by name

# Django shell
python manage.py shell
```

The settings module is split: `DJANGO_SETTINGS_MODULE` defaults to `backend.settings.dev` in development. The `dev.py` settings extend `base.py` and enable `DEBUG=True` and the DRF browsable API.

### Frontend (run from `frontend/`)

```bash
npm install
npm run dev      # development server on :3000
npm run build
npm run lint
npm run test     # vitest
npm run test:ui  # vitest with UI
```

### One-time setup (run once after cloning)

```bash
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
```

This activates the pre-commit hook that auto-bumps the minor version in `frontend/package.json` on every commit.

## Architecture

### Backend Django Apps

| App | Purpose |
|-----|---------|
| `research` | Core research jobs — models, LangGraph workflow, Gemini service |
| `ideation` | Use case and refined sales play generation (AGE-18, AGE-19) |
| `assets` | Asset generation — personas (AGE-21), one-pagers (AGE-22), account plans (AGE-23) |
| `projects` | Project/iteration workflow with context accumulation and work product tracking |
| `memory` | ChromaDB vector store for knowledge retention with deduplication guards |
| `prompts` | Configurable prompt template management |

### LangGraph Research Workflow

The AI pipeline in `research/graph/` runs these stages in sequence:

1. `validate` — check inputs and API key
2. `research` — Gemini deep research with Google Search grounding → `ResearchReport`
3. `classify` — industry vertical classification
4. `internal_ops` — internal operations intelligence research
5. `competitors` — competitor AI case studies
6. `gap_analysis` — technology and capability gap analysis
7. `correlate` — cross-reference gaps with internal ops evidence
8. `finalize` — persist all results to database

Each node receives and returns the full `ResearchState` dict. A `should_continue` conditional edge after each node exits early on `status == 'failed'`.

### Key Backend Service Files

- `research/services/gemini.py` — `GeminiClient` wrapping `google-genai`, handles structured output and grounding metadata
- `research/graph/nodes.py` — individual workflow node functions
- `research/graph/workflow.py` — `build_research_workflow()` compiles the LangGraph graph
- `ideation/services/` — `UseCaseGenerator`, `FeasibilityAssessor`, `PlayRefiner` for generating and refining sales plays
- `assets/services/` — `PersonaGenerator`, `OnePagerGenerator`, `AccountPlanGenerator`, `ExportService` for asset creation
- `projects/services/context.py` — `ContextAccumulator` for carrying research context between iterations
- `projects/services/comparison.py` — iteration diff/compare logic
- `memory/services/capture.py` — `MemoryCapture` with deduplication guards for safe insight storage
- `memory/services/vectorstore.py` — ChromaDB operations with collection management

### Settings Structure

`backend/backend/settings/base.py` → `dev.py` / `prod.py` using `django-environ`. All config via environment variables in `backend/.env`.

Required env vars: `SECRET_KEY`, `GEMINI_API_KEY`. Optional: `CHROMA_PERSIST_DIR`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`.

### API Endpoints Overview

**Ideation (AGE-18, AGE-19):**
- `POST /api/ideation/use-cases/generate/` — Generate use cases from research
- `GET /api/ideation/use-cases/?research_job=<id>` — List use cases
- `POST /api/ideation/use-cases/<id>/assess/` — Feasibility assessment
- `POST /api/ideation/use-cases/<id>/refine/` — Refine to sales play
- `GET /api/ideation/plays/<id>/` — Get refined play

**Assets (AGE-21, AGE-22, AGE-23):**
- `POST /api/assets/personas/generate/` — Generate personas
- `GET /api/assets/personas/?research_job=<id>` — List personas
- `POST /api/assets/one-pagers/generate/` — Generate one-pager
- `GET /api/assets/one-pagers/?research_job=<id>` — List one-pagers
- `POST /api/assets/account-plans/generate/` — Generate account plan
- `GET /api/assets/account-plans/?research_job=<id>` — List account plans

**Memory (AGE-14, AGE-17):**
- `POST /api/memory/capture/<job_id>/` — Auto-capture insights from completed research with deduplication

### Frontend Architecture

Next.js 14 App Router. API calls go through `frontend/lib/api.ts`. Types in `frontend/types/index.ts`. Backend URL configured via `NEXT_PUBLIC_API_URL` (default: `http://localhost:8000`).

**Toast Notification System:**
- `lib/toast.ts` — Toast context and hook (`useToast()`)
- `components/ui/Toast.tsx` — Toast renderer
- `app/Providers.tsx` — wraps app with Toast context
- `app/layout.tsx` — wrapped with Providers for Toast context

**Research Results Components:**
- `components/ResearchResults.tsx` — re-export barrel from decomposed module
- `components/research-results/index.tsx` — main ResearchResults component managing tabs
- `components/research-results/tabs/` — 8 tabs:
  - `ReportTab.tsx` — Company overview, decision makers, news
  - `SourcesTab.tsx` — Web sources from Google Search grounding
  - `InsideIntelTab.tsx` — Employee sentiment, LinkedIn, job postings, news sentiment, gap correlations
  - `CompetitorsTab.tsx` — Competitor case studies
  - `GapsTab.tsx` — Technology/capability/process gaps with recommendations
  - `RawTab.tsx` — Raw JSON output
  - `GenerateTab.tsx` (8th tab, blue pill) — Generate ideation and assets
- `components/research-results/generate/` — asset generation sections:
  - `UseCaseSection.tsx` — List and generate use cases
  - `PersonaSection.tsx` — List and generate buyer personas
  - `OnePagerSection.tsx` — List and generate one-pagers
  - `AccountPlanSection.tsx` — List and generate account plans
- `components/research-results/shared/` — shared utilities:
  - `StarOrSaveButton.tsx` — Conditional star/save button
  - `Section.tsx` — Common section wrapper
  - `MarkdownText.tsx` — Markdown renderer
  - `GapList.tsx` — Gap presentation helper
  - `InsideIntelHelpers.tsx` — Intel display helpers
  - `DetailRow.tsx` — Key-value detail display
  - `StatCard.tsx` — Stat card component

**Project/Iteration UI:**
- `app/research/[id]/page.tsx` — Research results page with polling cleanup
- `app/projects/[id]/page.tsx` — Project dashboard passing projectId + iterationId to ResearchResults

**Pages:**
- `/` — quick single research job
- `/research/[id]` — research job results with 8 tabs
- `/projects` — project list
- `/projects/new` — create project
- `/projects/[id]` — project dashboard
- `/projects/[id]/iterate` — run new iteration

## Recent Changes (Sprint Summary)

### Backend Updates
- **assets/views.py** — Added `AccountPlanListView` (GET /api/assets/account-plans/?research_job=<id>)
- **memory/services/capture.py** — Deduplication guard prevents duplicate MemoryEntry records for same research job/content
- **memory/services/vectorstore.py** — Removed deprecated `self.client.persist()` call (ChromaDB now auto-persists)
- **projects/models.py** — WorkProduct.project is now nullable; new optional research_job FK for standalone research work tracking; `CheckConstraint` enforces that at least one of project or research_job must be set (`workproduct_has_project_or_research_job`)
- **backend/settings/prod.py** — Production security hardening: HSTS, XSS filter, content-type nosniff, X-Frame-Options DENY, secure cookies, SSL redirect; startup `RuntimeError` raised if SECRET_KEY, ALLOWED_HOSTS, or CORS_ALLOWED_ORIGINS are missing
- **Test suite** — 280 backend tests collected (run with `pytest`)

### Frontend Updates
- **types/index.ts** — Added interfaces: UseCase, FeasibilityAssessment, RefinedPlay, Persona, OnePager, AccountPlan
- **lib/api.ts** — All ideation/assets/memory methods added (generateUseCases, generatePersonas, generateOnePager, generateAccountPlan, captureToMemory, etc.)
- **lib/toast.ts + components/ui/Toast.tsx + app/Providers.tsx** — Complete toast notification system
- **app/layout.tsx** — Wrapped with Providers for Toast context
- **components/ResearchResults.tsx** — Converted to 2-line barrel re-export
- **components/research-results/** — Fully decomposed into modular structure:
  - 8 tabs including new GenerateTab (blue pill style)
  - generate/ subdirectory with UseCaseSection, PersonaSection, OnePagerSection, AccountPlanSection
  - shared/ subdirectory with reusable components
  - ResearchCompletionBanner — dismissible banner on completed jobs
  - StarOrSaveButton — conditional star/save wrapper
  - SaveToDealModal — project picker/creator
- **app/research/[id]/page.tsx** — Polling cleanup fixed
- **app/projects/[id]/page.tsx** — Passes projectId + iterationId to ResearchResults
