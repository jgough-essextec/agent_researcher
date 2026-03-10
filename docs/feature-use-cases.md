# Feature: Use Case Generation

**Epic:** AGE-18
**App:** `ideation`
**Model:** `UseCase`
**Status:** Backend complete — No UI

---

## What It Is

Use Case Generation automatically produces 3–5 prioritised AI/technology use cases tailored to a specific prospect, based on the completed research for that company. Each use case describes a concrete opportunity for the sales team to propose an AI or technology solution that addresses a real, identified business problem.

This is the first step in the ideation pipeline. After research completes, the sales rep triggers use case generation to move from raw research intelligence into actionable sales plays.

---

## How It Is Supposed to Be Used

1. A research job completes (all 11 core pipeline calls have run).
2. The sales rep reviews the research output and decides to generate use cases.
3. They click a "Generate Use Cases" button on the research results page (not yet built).
4. The system calls `UseCaseGenerator.generate_use_cases()` using the research report, gap analysis, digital maturity, and AI adoption stage as context.
5. 3–5 use cases are returned, ranked by `impact_score` and `priority`.
6. The rep reviews the list and selects use cases to progress to Feasibility Assessment (`→ feature-feasibility.md`) or Play Refinement (`→ feature-refined-play.md`).
7. Use cases can be starred/saved to the project's Work Products sidebar via the `StarButton` component (built but currently unplaced).

---

## AI Generation

- **Service:** `ideation/services/use_case_generator.py`
- **Model:** `gemini-2.0-flash`
- **Prompt:** `USE_CASE_PROMPT`
- **Inputs to prompt:** client name, vertical, company overview, pain points, opportunities, digital maturity, AI adoption stage, gap analysis summary

---

## Database Fields

**Table:** `ideation_usecase`

| Field | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique identifier |
| `research_job` | FK → ResearchJob | The research job this use case was derived from |
| `title` | CharField (255) | Short descriptive name for the use case |
| `description` | TextField | Brief description of the use case |
| `business_problem` | TextField | The specific business problem being addressed |
| `proposed_solution` | TextField | Overview of the AI/technology solution proposed |
| `expected_benefits` | JSONField (list) | List of expected business benefits (strings) |
| `estimated_roi` | CharField (100) | e.g. "2-3x ROI within 12 months" |
| `time_to_value` | CharField (100) | e.g. "3-6 months" |
| `technologies` | JSONField (list) | Technologies involved e.g. ["LLM", "RAG", "Vector DB"] |
| `data_requirements` | JSONField (list) | Data sources or datasets needed |
| `integration_points` | JSONField (list) | Systems to integrate with e.g. ["Salesforce", "SAP"] |
| `priority` | CharField — `high` / `medium` / `low` | AI-assigned priority level |
| `impact_score` | FloatField (0.0–1.0) | AI-scored business impact |
| `feasibility_score` | FloatField (0.0–1.0) | Updated after feasibility assessment runs |
| `status` | CharField — `draft` / `validated` / `refined` / `approved` / `rejected` | Lifecycle state |
| `created_at` | DateTimeField | Auto-set on creation |
| `updated_at` | DateTimeField | Auto-updated on save |

---

## API Endpoints (Backend Only)

| Method | URL | Action |
|---|---|---|
| `GET` | `/api/ideation/use-cases/` | List all use cases |
| `POST` | `/api/ideation/use-cases/generate/` | Generate use cases from a research job |
| `GET` | `/api/ideation/use-cases/<id>/` | Retrieve a single use case |
| `POST` | `/api/ideation/use-cases/<id>/assess/` | Trigger feasibility assessment |
| `POST` | `/api/ideation/use-cases/<id>/refine/` | Trigger play refinement |

---

## UI Gap

- No "Generate Use Cases" button on any research results page
- No use case list or card view
- No use case detail page
- `api.ts` has zero calls to `/api/ideation/` endpoints
- `StarButton` component exists but is not placed anywhere
