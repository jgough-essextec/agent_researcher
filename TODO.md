# TODO — UI Build-Out for Backend-Complete Features

> Last updated: 2026-03-10
>
> The backend for the entire ideation, assets, and memory layers is feature-complete.
> The frontend has **zero calls** to any of these endpoints. This document tracks what
> needs to be built to surface this intelligence in the UI.
>
> Detailed feature documentation for each item lives in `docs/`.

---

## Summary of What Is Dark

| Feature | Backend | Frontend | Docs |
|---|---|---|---|
| Use Case Generation | ✅ Complete | ❌ None | `docs/feature-use-cases.md` |
| Feasibility Assessment | ✅ Complete | ❌ None | `docs/feature-feasibility.md` |
| Refined Sales Play | ✅ Complete | ❌ None | `docs/feature-refined-play.md` |
| Buyer Personas | ✅ Complete | ❌ None | `docs/feature-personas.md` |
| One-Pager Generator | ✅ Complete | ❌ None | `docs/feature-one-pager.md` |
| Account Plan Generator | ✅ Complete | ❌ None | `docs/feature-account-plan.md` |
| Citations | ✅ Complete | ❌ None | `docs/feature-citations.md` |
| Memory / Knowledge Base | ✅ Complete | ❌ None | `docs/feature-memory.md` |
| StarButton placement | ✅ Built | ❌ Never rendered | — |

---

## TODO Items

### 1. Use Case Generation
**Docs:** `docs/feature-use-cases.md`

**What is stored:** 3–5 AI-generated use cases per research job, each with a title, business problem, proposed solution, expected benefits, ROI estimate, time to value, required technologies, data requirements, integration points, priority level, and impact/feasibility scores.

**What needs to be built:**
- [ ] Add `api.ts` methods: `generateUseCases(researchJobId)`, `listUseCases(researchJobId)`, `getUseCase(id)`
- [ ] Add a **"Generate Use Cases"** button to the research results page (appears after research completes)
- [ ] Build a `UseCaseList` component showing use case cards ranked by priority and impact score
- [ ] Build a `UseCaseCard` component showing: title, business problem, proposed solution, benefits, ROI, time to value, priority badge, impact score, feasibility score
- [ ] Add status badge showing `draft / validated / refined / approved / rejected`
- [ ] Wire `StarButton` to use case cards so reps can save use cases to Work Products

---

### 2. Feasibility Assessment
**Docs:** `docs/feature-feasibility.md`

**What is stored:** Per-use-case technical feasibility verdict (low/medium/high), overall score, technical complexity narrative, data availability assessment, integration complexity, scalability notes, list of technical risks, mitigation strategies, prerequisites, dependencies, recommendations, and next steps.

**What needs to be built:**
- [ ] Add `api.ts` method: `assessFeasibility(useCaseId)`
- [ ] Add an **"Assess Feasibility"** button on each use case card
- [ ] Build a `FeasibilityPanel` component (expandable section within a use case card or a modal) showing:
  - Overall verdict badge (Low / Medium / High) with score percentage
  - Narrative sections: technical complexity, data availability, integration complexity, scalability
  - Technical risks list with corresponding mitigation strategies
  - Prerequisites and dependencies
  - Recommendations text
  - Next steps list
- [ ] Update use case status badge to `validated` after assessment runs

---

### 3. Refined Sales Play
**Docs:** `docs/feature-refined-play.md`

**What is stored:** Per-use-case sales play with an elevator pitch, value proposition, key differentiators, target persona, target vertical, company size fit, 3–5 discovery questions, 2–3 objection handlers (each with `{objection, response}`), proof points, competitive positioning, next steps, and success metrics.

**What needs to be built:**
- [ ] Add `api.ts` methods: `refinePlay(useCaseId)`, `getPlay(id)`, `listPlays()`
- [ ] Add a **"Refine Play"** button on validated use case cards
- [ ] Build a `PlayCard` component showing:
  - Elevator pitch (prominent, styled for readability)
  - Value proposition
  - Key differentiators as tags
  - Discovery questions as a numbered list
  - Objection handlers as an accordion (question → answer)
  - Proof points
  - Competitive positioning
  - Next steps and success metrics
  - Target persona, vertical, company size chips
- [ ] Place `StarButton` on play cards to save to Work Products sidebar
- [ ] Add status workflow controls: `draft → reviewed → approved → active`

---

### 4. Buyer Personas
**Docs:** `docs/feature-personas.md`

**What is stored:** 2–3 personas per research job, each with name, title, department, seniority level, background, goals, challenges, motivations, decision criteria, preferred communication style, typical objections, content preferences, and key messages.

**What needs to be built:**
- [ ] Add `api.ts` methods: `generatePersonas(researchJobId)`, `listPersonas(researchJobId)`, `getPersona(id)`
- [ ] Add a **"Generate Personas"** button to research results
- [ ] Build a `PersonaCard` component showing:
  - Name and title as the card header
  - Department and seniority level badges
  - Background narrative
  - Goals, challenges, motivations as lists
  - Decision criteria
  - Preferred communication style chip
  - Objections list (accordion or visible)
  - Content preferences as tags
  - Key messages highlighted prominently
- [ ] Place `StarButton` on persona cards
- [ ] Consider a side-by-side persona comparison view if multiple are generated

---

### 5. One-Pager Generator
**Docs:** `docs/feature-one-pager.md`

**What is stored:** A complete one-page sales document with title, headline, executive summary, challenge section, solution section, benefits section, differentiators list, call to action, next steps. Also has `html_content` and `pdf_path` fields for export.

**What needs to be built:**
- [ ] Add `api.ts` methods: `generateOnePager(researchJobId, useCaseId?)`, `getOnePager(id)`, `getOnePagerHtml(id)`
- [ ] Add a **"Generate One-Pager"** button (on research results, optionally linked to a use case)
- [ ] Build a `OnePagerPreview` component showing a styled document layout:
  - Large headline
  - Executive summary
  - Challenge / Solution / Benefits in a two or three column layout
  - Differentiators as a bullet list
  - Call to action and next steps at the bottom
- [ ] Add an **"Open HTML"** button that loads the `/html/` endpoint in a new tab or modal
- [ ] Add a **"Download PDF"** button (re-uses the PDF export pattern from research results)
- [ ] Place `StarButton` on one-pager preview
- [ ] Status badge: `draft / reviewed / approved / shared`

---

### 6. Account Plan Generator
**Docs:** `docs/feature-account-plan.md`

**What is stored:** A full strategic account plan with title, executive summary, account overview, strategic objectives, key stakeholders (with engagement approach per person), opportunity pipeline (with value/timeline/probability), competitive landscape, SWOT analysis, engagement strategy, value propositions, action plan (with owner/due date/status per item), success metrics, milestones, timeline. Also has `html_content` and `pdf_path`.

**What needs to be built:**
- [ ] Add `api.ts` methods: `generateAccountPlan(researchJobId)`, `getAccountPlan(id)`, `getAccountPlanHtml(id)`
- [ ] Add a **"Generate Account Plan"** button on research results or project dashboard
- [ ] Build an `AccountPlanView` — a multi-section document view:
  - Executive summary banner
  - Account overview section
  - Strategic objectives list
  - Key stakeholders table (name, title, decision role, engagement approach)
  - Opportunity pipeline table (name, value, timeline, probability)
  - SWOT analysis — 2×2 grid layout
  - Engagement strategy narrative
  - Value propositions
  - Action plan table (action, owner, due date, status)
  - Milestones timeline
  - Success metrics
- [ ] Add an **"Open HTML"** button and **"Download PDF"** button
- [ ] Status workflow: `draft → in_progress → reviewed → approved → active`
- [ ] Consider making the account plan the primary view for a project (not just a Work Product)

---

### 7. Citations
**Docs:** `docs/feature-citations.md`

**What is stored:** Structured source records with citation type (news/website/report/social/financial/press_release/other), title, source publication, URL, author, publication date, excerpt, relevance note, and a verification flag with verification date.

**What needs to be built:**
- [ ] Decide: should citations be auto-populated from `ResearchReport.web_sources` (grounding metadata), or remain manually managed?
- [ ] If auto-populating: build a migration/service to convert existing `web_sources` entries into `Citation` records
- [ ] Add `api.ts` methods: `listCitations(researchJobId)`, `getCitation(id)`
- [ ] Upgrade the existing **Sources tab** to display `Citation` records instead of raw `web_sources`, adding: source type badge, author, publication date, excerpt, relevance note, verification status badge
- [ ] Add a **"Verify"** button to mark a citation as verified

---

### 8. Memory / Knowledge Base
**Docs:** `docs/feature-memory.md`

**What is stored:** Three stores — `ClientProfile` (one per company, with industry, size, region, key contacts, full-text summary, and ChromaDB vector ID), `SalesPlay` (reusable plays tagged by type/vertical with usage count and success rate), and `MemoryEntry` (flexible knowledge records with type, content, tags, source reference, and vector ID).

**What needs to be built:**
- [ ] Add `api.ts` methods for all memory endpoints: `listProfiles()`, `getProfile(id)`, `listPlays()`, `getPlay(id)`, `listEntries()`, `getEntry(id)`, `queryContext(query)`
- [ ] Add a **Memory / Knowledge Base** page (new nav item):
  - **Client Profiles tab** — searchable list of all researched companies with their stored profile summaries
  - **Sales Play Library tab** — browsable/filterable list of reusable plays by type and vertical, showing usage count and success rate
  - **Memory Entries tab** — searchable feed of all captured insights, filterable by type and tag
- [ ] Add a **context search bar** to the research creation form: before starting a new job, query memory for prior context on that company and pre-populate the research with historical intelligence
- [ ] Add a **"Add to Play Library"** button on `RefinedPlay` cards to promote a play into `SalesPlay`
- [ ] Show memory capture confirmation in the research pipeline status (currently runs silently)

---

### 9. StarButton — Wire It Up
**What needs to be built:**
- [ ] Place `StarButton` on every generatable asset card: use cases, plays, personas, one-pagers
- [ ] Ensure the Work Products sidebar expands clicked items to show the full content (currently only shows title + summary preview)
- [ ] Add navigation from Work Products sidebar items to the full asset view

---

## Cross-Cutting Frontend Work

These items apply across multiple features above:

- [ ] **Add `ideation` and `assets` endpoints to `api.ts`** — none exist today
- [ ] **Add `memory` endpoints to `api.ts`** — none exist today
- [ ] **Add TypeScript types** for `UseCase`, `FeasibilityAssessment`, `RefinedPlay`, `Persona`, `OnePager`, `AccountPlan`, `Citation`, `ClientProfile`, `SalesPlay`, `MemoryEntry` to `frontend/types/index.ts`
- [ ] **Decide on navigation structure** — these features need a home in the nav. Options:
  - Add an "Ideation" tab to research results (alongside Overview, Deep Research, etc.)
  - Add an "Assets" section to the project dashboard sidebar
  - Create a standalone `/ideation` page
- [ ] **Mobile/responsive review** for all new components
