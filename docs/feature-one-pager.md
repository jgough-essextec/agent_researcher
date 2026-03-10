# Feature: One-Pager Generator

**Epic:** AGE-22
**App:** `assets`
**Model:** `OnePager`
**Status:** Backend complete — No UI

---

## What It Is

The One-Pager Generator creates a concise, customer-facing sales document tailored to a specific prospect. It distils the research intelligence — pain points, opportunities, and a chosen use case — into a single polished document that the sales rep can share with the prospect before or after a meeting.

The one-pager follows a standard structure: headline, challenge, solution, benefits, differentiators, and call to action. All content is specific to the named company, not generic product marketing.

An HTML render endpoint also exists so the one-pager can be formatted for professional export or email embedding.

---

## How It Is Supposed to Be Used

1. A research job completes, and optionally a use case has been generated.
2. The sales rep selects a use case (or proceeds without one for a general document) and clicks "Generate One-Pager" (not yet built).
3. The system calls `OnePagerGenerator.generate_one_pager()`.
4. The generated one-pager is stored and can be:
   - Viewed in the UI as a formatted document
   - Rendered as HTML via the `/html/` endpoint for email or browser presentation
   - Exported as PDF (the `pdf_path` field and export infrastructure exist)
   - Starred into the project's Work Products sidebar
5. The rep shares the one-pager with the prospect as pre-reading for a meeting or as a leave-behind.
6. Status can be progressed through `draft → reviewed → approved → shared`.

---

## AI Generation

- **Service:** `assets/services/one_pager.py`
- **Model:** `gemini-2.0-flash`
- **Prompt:** `ONE_PAGER_PROMPT`
- **Inputs to prompt:** client name, vertical, pain points, opportunities, use case title, proposed solution, expected benefits

---

## Database Fields

**Table:** `assets_onepager`

| Field | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique identifier |
| `research_job` | FK → ResearchJob | Research job the one-pager was created from |
| `title` | CharField (255) | Document title |
| `headline` | CharField (500) | Compelling headline capturing the core value proposition |
| `executive_summary` | TextField | 2–3 sentence summary for a time-poor executive |
| `challenge_section` | TextField | Description of the business challenges being addressed |
| `solution_section` | TextField | How the proposed solution addresses those challenges |
| `benefits_section` | TextField | Key benefits and expected outcomes |
| `differentiators` | JSONField (list) | 3–5 points that differentiate this solution |
| `call_to_action` | TextField | Clear, direct call to action |
| `next_steps` | JSONField (list) | Ordered list of recommended next steps |
| `html_content` | TextField | Rendered HTML version of the document (populated by `/html/` endpoint) |
| `pdf_path` | CharField (500) | File path to exported PDF (if generated) |
| `status` | CharField — `draft` / `reviewed` / `approved` / `shared` | Lifecycle state |
| `created_at` | DateTimeField | Auto-set on creation |
| `updated_at` | DateTimeField | Auto-updated on save |

---

## API Endpoints (Backend Only)

| Method | URL | Action |
|---|---|---|
| `GET` | `/api/assets/one-pagers/` | List all one-pagers |
| `POST` | `/api/assets/one-pagers/generate/` | Generate a one-pager from a research job |
| `GET` | `/api/assets/one-pagers/<id>/` | Retrieve a single one-pager |
| `GET` | `/api/assets/one-pagers/<id>/html/` | Retrieve HTML-rendered version |

---

## UI Gap

- No "Generate One-Pager" button anywhere
- No one-pager view or preview panel
- The HTML render endpoint exists but is never called
- PDF export infrastructure exists in the model but no UI trigger
- Work Products sidebar has `one_pager` category icon, but no one-pagers can be generated or starred
- `api.ts` has zero calls to `/api/assets/one-pagers/`
