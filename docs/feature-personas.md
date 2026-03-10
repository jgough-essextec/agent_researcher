# Feature: Buyer Persona Generation

**Epic:** AGE-21
**App:** `assets`
**Model:** `Persona`
**Status:** Backend complete — No UI

---

## What It Is

Buyer Persona Generation creates 2–3 detailed profiles of the key stakeholders the sales team is likely to encounter at a prospect company. Each persona is tailored to the specific company — drawing on identified decision makers, pain points, strategic goals, digital maturity, and industry vertical — rather than being a generic archetype.

Personas help sales reps understand who they are talking to, what that person cares about, how they make decisions, and what content or messaging will resonate with them. They are particularly useful for tailoring outreach, preparing for meetings, and aligning the sales play to the right audience.

---

## How It Is Supposed to Be Used

1. A research job completes.
2. The sales rep clicks "Generate Personas" on the research results (not yet built).
3. The system calls `PersonaGenerator.generate_personas()`, drawing on the research report's decision makers, pain points, strategic goals, and digital maturity.
4. 2–3 persona cards are generated and stored.
5. The rep uses personas to:
   - Tailor outreach messaging to the specific person's role and motivations
   - Prepare for objections they are likely to raise
   - Choose the right content format (whitepaper vs. demo vs. case study)
   - Brief other team members before meetings
6. Personas are linked to a research job and can be starred into the Work Products sidebar.

---

## AI Generation

- **Service:** `assets/services/persona.py`
- **Model:** `gemini-2.0-flash`
- **Prompt:** `PERSONA_PROMPT`
- **Inputs to prompt:** client name, vertical, decision makers (from research), pain points, strategic goals, digital maturity

---

## Database Fields

**Table:** `assets_persona`

| Field | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique identifier |
| `research_job` | FK → ResearchJob | The research job personas were derived from |
| `name` | CharField (255) | Persona archetype name e.g. "The Risk-Averse CFO" |
| `title` | CharField (255) | Job title e.g. "Chief Financial Officer" |
| `department` | CharField (100) | Department e.g. "Finance", "IT", "Operations" |
| `seniority_level` | CharField (50) | e.g. "C-Level", "VP", "Director", "Manager" |
| `background` | TextField | Brief professional background and career context |
| `goals` | JSONField (list) | What this persona is trying to achieve professionally |
| `challenges` | JSONField (list) | Pain points and obstacles they face day-to-day |
| `motivations` | JSONField (list) | What drives their decisions — career, company, personal |
| `decision_criteria` | JSONField (list) | What factors matter most when evaluating vendors/solutions |
| `preferred_communication` | CharField (100) | e.g. "Email", "In-person", "Video call", "Async" |
| `objections` | JSONField (list) | Common objections this persona typically raises |
| `content_preferences` | JSONField (list) | Preferred formats e.g. ["Whitepapers", "Case studies", "Live demos"] |
| `key_messages` | JSONField (list) | Messaging that resonates specifically with this persona |
| `created_at` | DateTimeField | Auto-set on creation |
| `updated_at` | DateTimeField | Auto-updated on save |

---

## API Endpoints (Backend Only)

| Method | URL | Action |
|---|---|---|
| `GET` | `/api/assets/personas/` | List all personas |
| `POST` | `/api/assets/personas/generate/` | Generate personas from a research job |
| `GET` | `/api/assets/personas/<id>/` | Retrieve a single persona |

---

## UI Gap

- No "Generate Personas" button on research results
- No persona card view
- No persona detail page
- Work Products sidebar has `persona` category icon, but personas cannot be generated or starred
- `api.ts` has zero calls to `/api/assets/personas/`
