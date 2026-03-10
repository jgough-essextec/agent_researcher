# Feature: Citations

**Epic:** AGE-24
**App:** `assets`
**Model:** `Citation`
**Status:** Backend complete — No UI

---

## What It Is

Citations are structured source references attached to a research job. They record the provenance of facts, claims, and data points used in the research output — similar to footnotes in an analyst report. Unlike the grounding metadata web sources (which are raw URLs returned by Google Search), Citations are enriched records with type classification, author, publication date, excerpt, and a relevance note explaining why this source was used.

Citations support the credibility of research outputs when sharing them with prospects or internal stakeholders who want to verify the intelligence.

---

## How It Is Supposed to Be Used

1. During or after research completes, citations are created to attribute source material.
2. Currently, this model appears to be intended for manual creation or population by the research pipeline — but **no service currently populates it automatically**. The Google Search grounding metadata is stored separately in `ResearchReport.web_sources`.
3. In the intended workflow, the citations list would appear as a references section at the bottom of research output documents, one-pagers, and account plans.
4. Citations can be marked `verified = True` once a human has confirmed the source is accurate and live.

---

## Database Fields

**Table:** `assets_citation`

| Field | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique identifier |
| `research_job` | FK → ResearchJob | Research job this citation belongs to |
| `citation_type` | CharField — `news` / `website` / `report` / `social` / `financial` / `press_release` / `other` | Type of source |
| `title` | CharField (500) | Title of the cited article or document |
| `source` | CharField (255) | Publication or domain name e.g. "TechCrunch", "Reuters" |
| `url` | URLField | Direct URL to the source |
| `author` | CharField (255) | Author name (if known) |
| `publication_date` | DateField | Date the source was published |
| `excerpt` | TextField | Relevant excerpt or quote from the source |
| `relevance_note` | TextField | Why this source is relevant to the research |
| `verified` | BooleanField | Whether the source has been manually verified as accurate and live |
| `verification_date` | DateTimeField | When the verification was performed |
| `created_at` | DateTimeField | Auto-set on creation |

---

## API Endpoints (Backend Only)

| Method | URL | Action |
|---|---|---|
| `GET` | `/api/assets/citations/` | List all citations |
| `GET` | `/api/assets/citations/<id>/` | Retrieve a single citation |

---

## Notes

- The existing `Sources` tab in the research results UI shows `ResearchReport.web_sources` — these are raw grounding URLs returned by Gemini's Google Search tool, not `Citation` records.
- `Citation` is a richer, more intentional model designed for curated attribution, but nothing currently populates it.
- There is no `POST /generate/` endpoint — citations are not AI-generated; they are expected to be created programmatically from the grounding data pipeline or manually.

---

## UI Gap

- No citations panel or references section
- The `Sources` tab shows raw grounding URLs but not `Citation` model records
- No verification workflow
- `api.ts` has zero calls to `/api/assets/citations/`
