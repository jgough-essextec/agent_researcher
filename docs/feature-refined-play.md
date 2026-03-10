# Feature: Refined Sales Play

**Epic:** AGE-20
**App:** `ideation`
**Model:** `RefinedPlay`
**Status:** Backend complete — No UI

---

## What It Is

A Refined Sales Play is a fully structured, ready-to-use sales playbook card generated from a validated use case. It translates the technical use case into practical sales enablement content — an elevator pitch, objection handlers, discovery questions, proof points, and competitive positioning — all tailored to the specific prospect.

The play is the "last mile" of the ideation pipeline: it turns research intelligence and a validated opportunity into something a sales rep can pick up and use in a customer conversation.

Each use case has exactly one refined play (1:1 relationship).

---

## How It Is Supposed to Be Used

1. A use case has been validated via feasibility assessment (see `feature-feasibility.md`), or can be refined directly from a draft use case.
2. The sales rep clicks "Refine Play" on a use case (not yet built).
3. The system calls `PlayRefiner.refine_play()`, pulling together the use case content, feasibility assessment, company digital maturity, and vertical context.
4. The play is generated and stored.
5. The rep uses the play as a reference card throughout the sales cycle:
   - **Elevator pitch** for first calls or introductions
   - **Discovery questions** to qualify the opportunity in meetings
   - **Objection handlers** to prepare for anticipated pushback
   - **Proof points** to back claims with evidence
   - **Competitive positioning** to differentiate against known alternatives
6. Plays can be starred into the project's Work Products sidebar.
7. The play status can be progressed through `draft → reviewed → approved → active → archived`.

---

## AI Generation

- **Service:** `ideation/services/play_refiner.py`
- **Model:** `gemini-2.0-flash`
- **Prompt:** `PLAY_REFINER_PROMPT`
- **Inputs to prompt:** use case title/description/problem/solution/benefits/ROI/time-to-value, client name, vertical, digital maturity, feasibility verdict, risks, recommendations

---

## Database Fields

**Table:** `ideation_refinedplay`

| Field | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique identifier |
| `use_case` | OneToOne FK → UseCase | The use case this play was generated from |
| `title` | CharField (255) | Play title |
| `elevator_pitch` | TextField | 30-second spoken pitch for introductory conversations |
| `value_proposition` | TextField | Detailed written value proposition |
| `key_differentiators` | JSONField (list) | What sets this solution apart from alternatives |
| `target_persona` | CharField (255) | Primary buyer persona this play targets |
| `target_vertical` | CharField (100) | Industry vertical the play is optimised for |
| `company_size_fit` | CharField (100) | e.g. "Enterprise", "Mid-market", "SMB" |
| `discovery_questions` | JSONField (list) | 3–5 questions to ask in discovery meetings |
| `objection_handlers` | JSONField (list) | List of `{objection: string, response: string}` objects |
| `proof_points` | JSONField (list) | Evidence statements, stats, or case study references |
| `competitive_positioning` | TextField | How to position against likely competitors |
| `next_steps` | JSONField (list) | Recommended follow-on actions after first meeting |
| `success_metrics` | JSONField (list) | How success would be measured if implemented |
| `status` | CharField — `draft` / `reviewed` / `approved` / `active` / `archived` | Lifecycle state |
| `created_at` | DateTimeField | Auto-set on creation |
| `updated_at` | DateTimeField | Auto-updated on save |

---

## API Endpoints (Backend Only)

| Method | URL | Action |
|---|---|---|
| `POST` | `/api/ideation/use-cases/<id>/refine/` | Generate a refined play from a use case |
| `GET` | `/api/ideation/plays/` | List all refined plays |
| `GET` | `/api/ideation/plays/<id>/` | Retrieve a single play |

---

## UI Gap

- No "Refine Play" button on use case cards
- No play card/detail view
- `StarButton` component is built but not placed anywhere — plays cannot be starred
- Work Products sidebar has a `play` category icon ready, but no plays can reach it
- `api.ts` has zero calls to `/api/ideation/plays/`
