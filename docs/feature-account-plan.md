# Feature: Account Plan Generator

**Epic:** AGE-23
**App:** `assets`
**Model:** `AccountPlan`
**Status:** Backend complete — No UI

---

## What It Is

The Account Plan Generator produces a comprehensive, structured strategic account plan for a prospect. This is a senior-level document — more detailed and strategic than a one-pager — intended to guide the entire sales engagement from initial contact through to close and beyond.

The account plan synthesises the full research output: company overview, decision makers, pain points, opportunities, competitor landscape, gap analysis findings, and strategic goals into a unified document with a SWOT analysis, stakeholder map, engagement strategy, and actionable milestones.

An HTML render endpoint also exists so the account plan can be formatted for professional presentation.

---

## How It Is Supposed to Be Used

1. A research job completes with a full set of data (report, gap analysis, competitor case studies ideally present).
2. The sales rep or account manager clicks "Generate Account Plan" (not yet built).
3. The system calls `AccountPlanGenerator.generate_account_plan()`, pulling in all available research data.
4. The account plan is stored and can be:
   - Viewed as a structured document in the UI
   - Rendered as HTML via the `/html/` endpoint
   - Exported as PDF (`pdf_path` field exists)
   - Starred into the Work Products sidebar
5. The account manager uses the plan to:
   - Align their team on the account strategy
   - Prepare executive briefings
   - Track milestones and action items
   - Brief leadership before QBRs or deal reviews
6. Status progresses through `draft → in_progress → reviewed → approved → active`.

---

## AI Generation

- **Service:** `assets/services/account_plan.py`
- **Model:** `gemini-2.0-flash`
- **Prompt:** `ACCOUNT_PLAN_PROMPT`
- **Inputs to prompt:** client name, vertical, company overview, decision makers, pain points, opportunities, strategic goals, digital maturity, competitor names (from case studies), gap analysis priority areas

---

## Database Fields

**Table:** `assets_accountplan`

| Field | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique identifier |
| `research_job` | OneToOne FK → ResearchJob | One account plan per research job |
| `title` | CharField (255) | Plan title e.g. "Account Plan: Acme Corp" |
| `executive_summary` | TextField | High-level summary of the account strategy |
| `account_overview` | TextField | Description of the account and current relationship status |
| `strategic_objectives` | JSONField (list) | Top 3–5 strategic objectives for the account |
| `key_stakeholders` | JSONField (list) | List of `{name, title, role_in_decision, engagement_approach}` objects |
| `opportunities` | JSONField (list) | List of `{name, value, timeline, probability}` opportunity objects |
| `competitive_landscape` | TextField | Analysis of competitive positioning for this account |
| `swot_analysis` | JSONField (dict) | `{strengths: [], weaknesses: [], opportunities: [], threats: []}` |
| `engagement_strategy` | TextField | Narrative description of the overall engagement approach |
| `value_propositions` | JSONField (list) | Key value propositions tailored to this account |
| `action_plan` | JSONField (list) | List of `{action, owner, due_date, status}` action items |
| `success_metrics` | JSONField (list) | How success is defined and measured |
| `milestones` | JSONField (list) | List of `{milestone, target_date, criteria}` milestone objects |
| `timeline` | TextField | Overall timeline narrative |
| `html_content` | TextField | Rendered HTML version of the document |
| `pdf_path` | CharField (500) | File path to exported PDF (if generated) |
| `status` | CharField — `draft` / `in_progress` / `reviewed` / `approved` / `active` | Lifecycle state |
| `created_at` | DateTimeField | Auto-set on creation |
| `updated_at` | DateTimeField | Auto-updated on save |

---

## API Endpoints (Backend Only)

| Method | URL | Action |
|---|---|---|
| `POST` | `/api/assets/account-plans/generate/` | Generate an account plan from a research job |
| `GET` | `/api/assets/account-plans/<id>/` | Retrieve a single account plan |
| `GET` | `/api/assets/account-plans/<id>/html/` | Retrieve HTML-rendered version |

---

## UI Gap

- No "Generate Account Plan" button anywhere
- No account plan view or section
- HTML render endpoint exists but is never called
- PDF export infrastructure exists in the model but is not triggered
- `api.ts` has zero calls to `/api/assets/account-plans/`
