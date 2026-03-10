# Feature: Feasibility Assessment

**Epic:** AGE-19
**App:** `ideation`
**Model:** `FeasibilityAssessment`
**Status:** Backend complete — No UI

---

## What It Is

Feasibility Assessment evaluates the technical viability of a given use case. It analyses the proposed solution against the company's current digital maturity, AI adoption stage, and the technical complexity of the implementation to produce an honest, risk-aware assessment that helps the sales rep understand whether a use case is immediately deliverable or requires significant groundwork.

Each use case has exactly one feasibility assessment (1:1 relationship).

---

## How It Is Supposed to Be Used

1. A use case has been generated (see `feature-use-cases.md`).
2. The sales rep selects a use case and clicks "Assess Feasibility" (not yet built).
3. The system calls `FeasibilityService.assess_feasibility()`, passing the use case details and company context.
4. The assessment is saved and displayed alongside the use case.
5. The rep uses the feasibility output to:
   - Qualify whether to pursue the use case further
   - Understand what prerequisites must be in place before pitching
   - Identify technical risks to address in discovery conversations
6. Once assessed, the use case status transitions to `validated`.
7. The rep can then proceed to Play Refinement (see `feature-refined-play.md`).

---

## AI Generation

- **Service:** `ideation/services/feasibility.py`
- **Model:** `gemini-2.0-flash`
- **Prompt:** `FEASIBILITY_PROMPT`
- **Inputs to prompt:** use case title, description, business problem, proposed solution, technologies, data requirements, integration points, industry vertical, digital maturity, AI adoption stage

---

## Database Fields

**Table:** `ideation_feasibilityassessment`

| Field | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique identifier |
| `use_case` | OneToOne FK → UseCase | The use case being assessed |
| `overall_feasibility` | CharField — `low` / `medium` / `high` | Summary feasibility verdict |
| `overall_score` | FloatField (0.0–1.0) | Numeric feasibility score |
| `technical_complexity` | TextField | Narrative assessment of technical difficulty |
| `data_availability` | TextField | Assessment of whether required data is accessible |
| `integration_complexity` | TextField | Assessment of integration effort with existing systems |
| `scalability_considerations` | TextField | Notes on scaling the solution once live |
| `technical_risks` | JSONField (list) | List of identified technical risks (strings) |
| `mitigation_strategies` | JSONField (list) | Corresponding risk mitigation approaches (strings) |
| `prerequisites` | JSONField (list) | What must be in place before implementation can start |
| `dependencies` | JSONField (list) | External systems, data, or teams required |
| `recommendations` | TextField | Overall recommendation narrative |
| `next_steps` | JSONField (list) | Ordered list of recommended next actions |
| `created_at` | DateTimeField | Auto-set on creation |
| `updated_at` | DateTimeField | Auto-updated on save |

---

## API Endpoints (Backend Only)

| Method | URL | Action |
|---|---|---|
| `POST` | `/api/ideation/use-cases/<id>/assess/` | Run feasibility assessment for a use case |

Assessment results are returned inline with the use case detail response.

---

## UI Gap

- No "Assess Feasibility" button
- No feasibility results panel or card
- Assessment data is generated and stored but never retrieved by the frontend
- `api.ts` has zero calls to this endpoint
