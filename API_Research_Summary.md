# API & Model Research Summary

> Deep Prospecting Engine — GCP / Gemini API Usage Reference
> Last updated: 2026-03-10

---

## 1. GCP Services in Use

| Dimension | Value |
|---|---|
| **GCP Service** | Gemini API (via `google-genai` Python SDK) |
| **Model** | `gemini-2.0-flash` — used by every single call in the system |
| **Authentication** | API key (`GEMINI_API_KEY` env var) — direct key auth, **not** Vertex AI / ADC |
| **Other AI providers** | None — Gemini is the only model in the system |
| **Other GCP services** | None currently — no Cloud Run, no GCS, no Vertex AI endpoints |

**SDK initialisation** (`research/services/gemini.py:283`):
```python
from google import genai
self._client = genai.Client(api_key=self.api_key)
```

---

## 2. Two Call Types

All Gemini calls are made through `GeminiClient` in `research/services/gemini.py`.

### Type A — Grounded (Google Search enabled)
Used **only in Phase 1 of the research pipeline**.
Attaches `GoogleSearch` as a tool so Gemini can pull live web data and return grounding metadata (source URLs + search queries used).

```python
response = self.client.models.generate_content(
    model='gemini-2.0-flash',
    contents=prompt,
    config=types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
    ),
)
```

### Type B — Plain completion (no grounding)
Used by every other service via `GeminiClient.generate_text(prompt)`:
```python
response = self.client.models.generate_content(
    model='gemini-2.0-flash',
    contents=prompt,
)
```

---

## 3. Full Agent / Service → API Call → UI Panel Map

### 3.1 Core Research Pipeline (runs automatically on every job)

| # | Agent / Service | File | Call Type | Prompt | What It Does | UI Location |
|---|---|---|---|---|---|---|
| 1a | Parallel Grounded Query: **Profile** | `gemini.py:362` | **Type A** (grounded) | `PROFILE_QUERY_PROMPT` | Fetches company overview, HQ, revenue, employee count, founding year | `Overview` tab → Company Overview, Quick Stats cards, `Deep Research` tab → Company Details |
| 1b | Parallel Grounded Query: **News** | `gemini.py:363` | **Type A** (grounded) | `NEWS_QUERY_PROMPT` | Recent news headlines, dates, sources | `Deep Research` tab → Recent News section |
| 1c | Parallel Grounded Query: **Leadership** | `gemini.py:364` | **Type A** (grounded) | `LEADERSHIP_QUERY_PROMPT` | Executive names, titles, backgrounds | `Overview` tab → Key Decision Makers section |
| 1d | Parallel Grounded Query: **Technology** | `gemini.py:365` | **Type A** (grounded) | `TECHNOLOGY_QUERY_PROMPT` | Tech stack, digital maturity, AI adoption | `Overview` tab → Digital Maturity stat card; `Deep Research` tab → Digital & AI Assessment |
| 2 | **Synthesis** | `gemini.py:477` | Type B (plain) | `SYNTHESIS_PROMPT` | Combines the 4 parallel results into a narrative | Not directly displayed — feeds Phase 3 |
| 3 | **JSON Formatter** | `gemini.py:488` | Type B (plain) | `JSON_FORMAT_PROMPT` | Converts narrative to structured JSON | All structured fields in `Overview` and `Deep Research` tabs |
| 4 | **Vertical Classifier** | `gemini.py:534`, `classifier.py:113` | Type B (plain) | `VERTICAL_CLASSIFICATION_PROMPT` | Classifies company into 1 of 18 industry verticals | Research results header — industry label below company name; also `Deep Research` tab header |
| 5 | **Competitor Search** | `competitor.py:88` | Type B (plain) | `COMPETITOR_SEARCH_PROMPT` | Finds 3–5 competitor AI case studies with relevance scores | `Competitors` tab — each card shows company, vertical, case study title, technologies, outcomes, % relevance match |
| 6 | **Gap Analysis** | `gap_analysis.py:106` | Type B (plain) | `GAP_ANALYSIS_PROMPT` | Identifies technology, capability, and process gaps | `Gap Analysis` tab — Priority Areas, Technology Gaps (red), Capability Gaps (orange), Process Gaps (purple), Recommendations, confidence % |
| 7 | **Internal Ops Research** | `internal_ops.py:298` | Type B (plain) | `INTERNAL_OPS_PROMPT` | Employee sentiment, LinkedIn presence, job postings, social media, news sentiment | `Inside Intel` tab — 6 sections (see §3.2 below) |
| 8 | **Gap Correlation** | `gap_correlation.py:170` | Type B (plain) | `GAP_CORRELATION_PROMPT` | Cross-references gaps with internal ops evidence | `Inside Intel` tab → **Gap Correlation Insights** section — each card shows gap type, evidence, evidence type badge (supporting/contradicting/neutral), confidence %, sales implication |

**Grounding metadata** (web sources collected from Type A calls):
→ `Sources` tab — numbered list of every URL used as a grounding source, with title and clickable link

**Raw output** (plain-text rendering of the full research report):
→ `Raw Output` tab

---

### 3.2 Inside Intel Tab — Detailed Sub-Panel Mapping

The `Inside Intel` tab (`InsideIntelTab` component, `ResearchResults.tsx:435`) is populated entirely by `InternalOpsService` and `GapCorrelationService`.

| Section in UI | Data Field | Source Service |
|---|---|---|
| **Employee Sentiment Overview** | `employee_sentiment` (rating, categories, recommend %, trend, themes) | `InternalOpsService` |
| **Talent & Hiring Intelligence** | `job_postings` (openings, departments, skills, seniority, urgency signals) | `InternalOpsService` |
| **Digital & Social Presence** | `linkedin_presence` (followers, engagement, recent posts, notable changes) | `InternalOpsService` |
| **Social Media Mentions** | `social_media_mentions` (platform, summary, sentiment, topic) | `InternalOpsService` |
| **News Coverage** | `news_sentiment` (sentiment, volume, topics, headlines) | `InternalOpsService` |
| **Gap Correlation Insights** | `gap_correlations` (gap_type, description, evidence, evidence_type, confidence, sales_implication) | `GapCorrelationService` |
| **Key Insights & Recommendations** | `key_insights` | `InternalOpsService` |
| Footer metadata | `confidence_score`, `data_freshness`, `analysis_notes` | `InternalOpsService` |

---

### 3.3 On-Demand Asset Generation (user-triggered, not part of core pipeline)

These services are called explicitly by the user via API endpoints — they do not run automatically.

| Agent / Service | File | Prompt | What It Generates | UI Location |
|---|---|---|---|---|
| **Use Case Generator** | `use_case_generator.py:112` | `USE_CASE_PROMPT` | 3–5 AI use cases with ROI, timeline, technologies, feasibility score | Ideation section — use case cards (not yet surfaced in a dedicated page; stored in DB) |
| **Feasibility Service** | `feasibility.py:126` | `FEASIBILITY_PROMPT` | Technical feasibility assessment per use case (score, risks, mitigation, prerequisites) | Linked to each use case; stored as `FeasibilityAssessment` model |
| **Play Refiner** | `play_refiner.py:129` | `PLAY_REFINER_PROMPT` | Sales play per use case: elevator pitch, objection handlers, discovery questions, proof points | Work Products sidebar in Project Dashboard → `play` category items |
| **Persona Generator** | `persona.py:117` | `PERSONA_PROMPT` | 2–3 buyer personas with goals, challenges, objections, key messages | Work Products sidebar → `persona` category items |
| **One-Pager Generator** | `one_pager.py:97` | `ONE_PAGER_PROMPT` | 1-page sales document: headline, challenge, solution, benefits, CTA | Work Products sidebar → `one_pager` category items |
| **Account Plan Generator** | `account_plan.py:149` | `ACCOUNT_PLAN_PROMPT` | Full strategic account plan: SWOT, stakeholder map, action plan, milestones | Work Products sidebar → displayed as saved work product under project |

---

## 4. Total Gemini API Calls Per Research Job

### Automatic (core pipeline)
```
Phase 1 — Grounded queries (parallel, 4 threads):
  ├── profile     →  1 grounded call
  ├── news        →  1 grounded call
  ├── leadership  →  1 grounded call
  └── technology  →  1 grounded call

Phase 2 — Synthesis              →  1 plain call
Phase 3 — JSON formatting        →  1 plain call
Vertical classification          →  1 plain call
Competitor search                →  1 plain call
Gap analysis                     →  1 plain call
Internal ops research            →  1 plain call
Gap correlation                  →  1 plain call
─────────────────────────────────────────────────
Core pipeline total:             11 Gemini API calls
```

### On-demand (user-triggered, per action)
```
Use case generation              →  1 call
Feasibility assessment           →  1 call per use case
Play refinement                  →  1 call per use case
Persona generation               →  1 call
One-pager generation             →  1 call
Account plan generation          →  1 call
```

---

## 5. UI Page → Tab → Data Source Reference

| Page / Route | Tab / Panel | Backend Data | Source Service(s) |
|---|---|---|---|
| `/` or `/research/[id]` | **Overview** | `report.company_overview`, `founded_year`, `employee_count`, `annual_revenue`, `digital_maturity`, `decision_makers`, `pain_points`, `opportunities`, `talking_points` | GeminiClient Phase 1–3 |
| `/research/[id]` | **Deep Research** | `report.headquarters`, `website`, `founded_year`, `employee_count`, `annual_revenue`, `digital_maturity`, `ai_adoption_stage`, `ai_footprint`, `recent_news`, `strategic_goals`, `key_initiatives` | GeminiClient Phase 1–3 |
| `/research/[id]` | **Competitors** | `competitor_case_studies[]` | CompetitorSearchService |
| `/research/[id]` | **Gap Analysis** | `gap_analysis` (technology_gaps, capability_gaps, process_gaps, recommendations, priority_areas) | GapAnalysisService |
| `/research/[id]` | **Inside Intel** | `internal_ops` + `gap_correlations` | InternalOpsService + GapCorrelationService |
| `/research/[id]` | **Sources** | `report.web_sources[]` (uri, title) | GeminiClient Type A grounding metadata |
| `/research/[id]` | **Raw Output** | `job.result` (plain text) | GeminiClient Phase 3 (formatted) |
| `/projects/[id]` | Research content area | Same as `/research/[id]` tabs — rendered via `ResearchResults` component | All of the above |
| `/projects/[id]` | **Saved sidebar** | `work_products[]` — play, persona, one_pager, use_case, gap, insight | PlayRefiner, PersonaGenerator, OnePagerGenerator, AccountPlanGenerator, UseCaseGenerator |
| `/projects/[id]` | **Notes sidebar** | `annotations[]` — user-created notes | No AI — pure user input |

---

## 6. Key Architecture Notes

- **No Vertex AI**: Authentication is via raw API key, not Google Application Default Credentials (ADC) or a Vertex AI endpoint. If deploying to GCP, consider migrating to Vertex AI for IAM-based auth.
- **One model, one version**: `gemini-2.0-flash` is hardcoded in every call — there is no model routing or fallback. Version pinning is implicit (not specifying `-preview` or a specific version hash).
- **Parallelism**: Phase 1 uses `ThreadPoolExecutor(max_workers=4)` for the 4 grounded queries. All other calls are sequential within the LangGraph pipeline.
- **No streaming**: All calls use `generate_content` (synchronous, full response). There is no streaming to the frontend.
- **JSON parsing pattern**: Every service strips markdown code fences before `json.loads()`. This is a known fragility — Gemini occasionally wraps JSON in ` ```json ` blocks despite instructions.
- **Grounding metadata deduplication**: Web sources are deduplicated by URI before storage (`_merge_grounding_metadata`).
