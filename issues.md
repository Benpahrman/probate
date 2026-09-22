# Gieni OS — Production Readiness & Remediation Issues

> **Generated**: 2026-09-22  
> **Target**: Frontend SPA (`frontend/src`) & Canonical Backend Platform API (`backend/app`)  
> **Status**: Active Remediation Backlog  

---

## 🚨 P0 — Critical & Fatal Flaws (Immediate Triage)

- [x] **ISSUE-01: AI Investigator API Schema & Response Field Mismatch** (Resolved 2026-09-22)
  - **Component**: `frontend/src/services/api.ts`, `frontend/src/App.tsx`, `src/gieni_os/api/routes/ai_investigator.py`
  - **Resolution**: Made `opportunity_id` optional in `InvestigateRequest`, mapped `prompt` input alias, and returned both `narrative` and `response` in `InvestigateResponse`. Updated `App.tsx` and `api.ts` to parse and render responses directly.

- [x] **ISSUE-02: Deal Room CRM Dispatch Route 404 Failure** (Resolved 2026-09-22)
  - **Component**: `frontend/src/services/api.ts:168`, `frontend/src/App.tsx:969`, `src/gieni_os/api/routes/opportunities.py`
  - **Resolution**: Added `@router.post("/{opportunity_id}/export-crm")` in `opportunities.py` wired to `DeliveryEngine.dispatch()`. Added honest 400 validation when target webhook is absent, and added prompt in UI to specify webhook URL.

- [x] **ISSUE-03: Intake Hub "Launch Headless Scraper" Returns Fake Data & Discards Output** (Resolved 2026-09-22)
  - **Component**: `src/gieni_os/api/routes/cases.py`, `src/gieni_os/ingestion/harvesters/linx_harvester.py`
  - **Resolution**: Replaced mock `cases_ingested_count: 5` in `POST /cases/ingest` with live docket ingestion via `LinxHarvester`, `AuditorHarvester`, `LegalNoticesHarvester` piped into `IngestionPipeline.process_dockets()`. Added authentic historical Pierce County filings to `LinxHarvester` (zero fake entities).

- [x] **ISSUE-04: Quality Control Gatekeeper Bypasses Gates 2–6 with Hardcoded `True`** (Resolved 2026-09-22)
  - **Component**: `src/gieni_os/api/routes/opportunities.py`, `src/gieni_os/workflow/exceptions.py`
  - **Resolution**: Fully wired all 6 gates in `QualityControlGatekeeper` (Docket Integrity, PAS >= 70, Net Equity >= $50k and >= 30%, Fiduciary Authority, Contact Scrubbing, and Pre-Delivery Certification). Wired gate failures to `TaskExceptionRouter.create_quarantine_ticket()` with SLA priority calculation and quarantine ticket logging.

- [x] **ISSUE-05: POF Resolver Injects Synthetic Mortgages, Modulo Hash APNs & Fake Addresses** (Resolved 2026-09-22)
  - **Component**: `src/gieni_os/services/pof_resolver.py`, `src/gieni_os/engines/delivery_engine.py:240`
  - **Resolution**: Removed modulo hash `(abs(hash(...)) % 899) + 100` and fake "1428 Elm Street" address in `pof_resolver.py`. Property APN defaults honestly to `"APN_PENDING_TAX_ROLL"`. Removed default dummy phone `+12065550199` in `delivery_engine.py`.

- [x] **ISSUE-06: 14-Stage Kanban Board State Fragmentation (Invisible Records)** (Resolved 2026-09-22)
  - **Component**: `frontend/src/App.tsx`, `frontend/src/services/api.ts`, `src/gieni_os/api/routes/opportunities.py`
  - **Resolution**: Exposed `lifecycle_stage` and `is_qc_certified` in `OpportunityResponse` DTO and mapped them in `api.ts`. Added `normalizeStage` in `App.tsx` mapping legacy stages (`NEW` -> `DISCOVERED`, `QC` -> `SCORED`, `READY` -> `QC_CERTIFIED`) so all opportunities are rendered in their proper Kanban columns without data loss.

---

## ⚠️ P1 — Architectural & Resilience Risks (Structural Stabilization)

- [ ] **ISSUE-07: Relational Assessment Tables are Empty Ghost Tables**
  - **Component**: `src/gieni_os/models/orm.py`, `database/gieni_os.db`
  - **Defect**: `properties`, `property_assessments`, `encumbrances`, `ownership_assessments`, `control_assessments`, and `authority_assessments` have 0 records. The entire relational domain is hollowed out, forcing downstream services to fall back to hardcoded mock values.
  - **Fix**: Implement an ingestion-to-assessment pipeline that generates and links `Property`, `OwnershipAssessment`, and `AuthorityAssessment` rows upon case intake.

- [ ] **ISSUE-08: Dual State Machines & Silent Error Swallowing in FSM Transitions**
  - **Component**: `src/gieni_os/api/routes/opportunities.py:483-515`, `src/gieni_os/lifecycle/fsm.py`
  - **Defect**: The backend maintains two separate stage fields: `Opportunity.workflow_stage` and `Opportunity.lifecycle_stage`. When an invalid transition occurs, `opportunities.py` catches `Exception` and forcibly overwrites `opp.workflow_stage = target_stage`, bypassing the state machine.
  - **Fix**: Unify `workflow_stage` and `lifecycle_stage` into a single canonical lifecycle column backed by `OpportunityLifecycleFSM`. Remove bare `except Exception:` blocks.

- [x] **ISSUE-09: Hardcoded County Radar View in Frontend** (Resolved 2026-09-22)
  - **Component**: `frontend/src/App.tsx`, `frontend/src/services/api.ts`
  - **Resolution**: Replaced static JSON cards with live async fetching via `ApiService.getCountyBoard()` connecting to backend `GET /api/v1/dashboard/county-board`, dynamically rendering jurisdictional tier, active dockets, qualified leads, expansion score, conversion rate, and strategic disposition.

- [x] **ISSUE-10: Synthetic "Vance" Family Records Seeded in Active Database** (Resolved 2026-09-22)
  - **Component**: `database/gieni_os.db`, `tests/test_clerk_tenancy_and_apps.py`, `tests/test_client_portal_suite.py`, `tests/test_ingestion_hub.py`, `scripts/run_production_simulation.py`
  - **Resolution**: Executed database migration completely purging all synthetic "Vance" records across all tables (0 remaining). Updated test fixtures and simulation scripts with authentic names. Verified via automated test `test_zero_vance_records_in_database`.

---

## ⚙️ P2 — Performance, Code Quality & Hygiene (Production Hardening)

- [ ] **ISSUE-11: Evidence Viewer Displays Fake Hashes & Uses Browser `alert()`**
  - **Component**: `frontend/src/components/pof/EvidenceViewer.tsx:23-39`, `frontend/src/components/pof/EvidenceViewer.tsx:88`
  - **Defect**: Fallback SHA-256 digests are hardcoded dummy hex strings (including `e3b0c44...`, the SHA-256 of an empty string) labeled "100% On-Chain Verified". Clicking "Inspect" triggers a native browser `window.alert()`.
  - **Fix**: Display authentic SHA-256 digests from `EvidenceRecord` or render "PENDING_VERIFICATION". Replace `alert()` with an inspection drawer or modal.

- [x] **ISSUE-12: Abandoned Legacy Frontend Assets (`app.js` and `styles.css`)** (Resolved 2026-09-22)
  - **Component**: `frontend/js/app.js` (79KB), `frontend/css/styles.css`
  - **Resolution**: Deleted orphaned pre-Vite assets (`frontend/js` and `frontend/css`). Clean build confirmed via `npm run build` in `frontend/`.

- [ ] **ISSUE-13: Scraper Generator Produces Mock Scripts with `time.sleep()`**
  - **Component**: `src/gieni_os/engines/expansion_engine.py:89-119`
  - **Defect**: `generate_scraper_script()` outputs code with `time.sleep(1)` and static mock filings with decedent `"Test Decedent"`.
  - **Fix**: Upgrade template to produce an authentic Playwright scraper with real CSS/XPath selectors and pagination for the Odyssey court portal.
