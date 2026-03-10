# Feature: Memory & Knowledge Base

**Epics:** AGE-14 (vector store), AGE-15 (client profiles), AGE-16 (sales plays), AGE-17 (auto-capture)
**App:** `memory`
**Models:** `ClientProfile`, `SalesPlay`, `MemoryEntry`
**Status:** Backend complete — No UI

---

## What It Is

The Memory system is a persistent knowledge base backed by ChromaDB (a vector database). It automatically captures intelligence from every completed research job and stores it in a way that can be semantically queried in future sessions. This means the system learns over time: the more research is run, the richer the context available for future engagements.

The memory layer has three distinct components:

1. **Client Profiles** — Structured profiles of every company researched, stored as embeddings for similarity search.
2. **Sales Plays** — A library of reusable sales plays (pitches, objection handlers, discovery questions, value propositions, competitive responses), tagged by vertical and industry, with effectiveness tracking.
3. **Memory Entries** — A flexible store for any knowledge the system or user wants to persist: research insights, deal outcomes, best practices, lessons learned.

Auto-capture runs at the end of every research pipeline (`finalize_result` node in `research/graph/nodes.py`) via `MemoryCapture.capture_from_research()`.

---

## How It Is Supposed to Be Used

### Auto-Capture (already running)
Every time a research job completes, the system automatically:
- Creates or updates a `ClientProfile` for the company researched
- Creates `MemoryEntry` records for key insights from the research

### Context Query (not wired to UI)
Before starting a new research job for a previously researched company, the system can query the memory store to retrieve relevant prior intelligence. This enriches the new research with historical context — previous pain points, past interactions, deal history patterns. The endpoint `/api/memory/context/` accepts a query and returns semantically similar memory entries.

### Sales Play Library (not wired to UI)
As refined plays are generated via the ideation pipeline, the best plays can be promoted into the `SalesPlay` model for reuse across all reps and all prospects. A rep could query "show me all objection handlers for retail finance" and get the highest-success-rate plays back.

### Manual Capture
The endpoint `/api/memory/capture/<research_job_id>/` allows triggering a manual capture from a completed research job.

---

## Database Models

### ClientProfile
**Table:** `memory_clientprofile`

| Field | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique identifier |
| `client_name` | CharField (255, unique) | Company name — one profile per company |
| `industry` | CharField (100) | Industry vertical |
| `company_size` | CharField (50) | Size descriptor e.g. "Enterprise", "5,000–10,000 employees" |
| `region` | CharField (100) | Geographic region |
| `key_contacts` | JSONField (list) | List of key contacts from research |
| `summary` | TextField | Full-text summary used to generate the embedding |
| `vector_id` | CharField (255) | ChromaDB document ID for the embedding |
| `created_at` | DateTimeField | Auto-set on creation |
| `updated_at` | DateTimeField | Auto-updated on save |

---

### SalesPlay
**Table:** `memory_salesplay`

| Field | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique identifier |
| `title` | CharField (255) | Play title |
| `play_type` | CharField — `pitch` / `objection_handler` / `value_proposition` / `case_study` / `competitive_response` / `discovery_question` | Type of sales play |
| `content` | TextField | The full play content — the actual text to use |
| `context` | TextField | Guidance on when and how to use this play |
| `industry` | CharField (100) | Industry this play was written for |
| `vertical` | CharField (50) | Specific vertical e.g. "healthcare", "finance" |
| `usage_count` | IntegerField | How many times this play has been used |
| `success_rate` | FloatField (0.0–1.0) | Effectiveness score (intended for tracking over time) |
| `vector_id` | CharField (255) | ChromaDB document ID for semantic retrieval |
| `created_at` | DateTimeField | Auto-set on creation |
| `updated_at` | DateTimeField | Auto-updated on save |

---

### MemoryEntry
**Table:** `memory_memoryentry`

| Field | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique identifier |
| `entry_type` | CharField — `research_insight` / `client_interaction` / `deal_outcome` / `best_practice` / `lesson_learned` | Type of memory |
| `title` | CharField (255) | Short title for the memory entry |
| `content` | TextField | Full text of the memory — used to generate the embedding |
| `client_name` | CharField (255) | Company this memory relates to (if applicable) |
| `industry` | CharField (100) | Industry context |
| `tags` | JSONField (list) | Free-form tags for filtering e.g. ["AI adoption", "cost pressure"] |
| `source_type` | CharField (50) | Where this came from e.g. "research_job", "manual" |
| `source_id` | CharField (255) | ID of the source record (e.g. the ResearchJob UUID) |
| `vector_id` | CharField (255) | ChromaDB document ID for semantic retrieval |
| `created_at` | DateTimeField | Auto-set on creation |
| `updated_at` | DateTimeField | Auto-updated on save |

---

## API Endpoints (Backend Only)

| Method | URL | Action |
|---|---|---|
| `GET` | `/api/memory/profiles/` | List all client profiles |
| `GET` | `/api/memory/profiles/<id>/` | Retrieve a single client profile |
| `GET` | `/api/memory/plays/` | List all sales plays in the library |
| `GET` | `/api/memory/plays/<id>/` | Retrieve a single sales play |
| `GET` | `/api/memory/entries/` | List all memory entries |
| `GET` | `/api/memory/entries/<id>/` | Retrieve a single memory entry |
| `POST` | `/api/memory/context/` | Query memory store for relevant context (semantic search) |
| `POST` | `/api/memory/capture/<id>/` | Manually trigger capture from a research job |

---

## UI Gap

- No memory browser or knowledge base view anywhere
- Auto-capture runs silently on every job — data accumulates but is invisible
- No way to view, search, or query the memory store
- No sales play library browser
- No mechanism to promote a refined play into the reusable sales play library
- `api.ts` has zero calls to `/api/memory/`
