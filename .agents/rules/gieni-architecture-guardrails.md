# Gieni OS Architectural Guardrails & Invariants

## 1. Zero Custom Auth (Clerk Identity & Tenancy Invariant)
- **NEVER** design, propose, or build custom authentication, user tables, password resets, session management, or JWT rotation.
- **Clerk** is the sole identity and multi-tenancy layer.
- **Tenancy Boundary**:
  - 1 Clerk Organization = 1 Wholesaler Customer.
  - Multi-tenancy isolation is enforced by mapping `x-clerk-org-id` to County Contracts (`ClientModel.county_id`).
  - Opportunities are strictly partitioned by jurisdiction contracts. Operators without org scope act under global platform tenancy.

## 2. Extensible Provider Architecture for Research & Intelligence
- All intelligence domains (Contacts/Skip-Trace, Title/Deeds/Liens, Authority/Probate, Valuation/Comps) MUST inherit from `BaseResearchProvider` and register into `ResearchHubService`.
- **Zero Core Refactoring**: Connecting external vendors (e.g. Attom Data, CoreLogic, BatchData, LexisNexis) must require only subclassing `BaseResearchProvider` and calling `ResearchHubService.register_provider()`.
- **Multi-Surface Accessibility**: Research capabilities must never be locked to a single view. They must be accessible via:
  1. REST API (`/api/research/*`)
  2. Opportunity Workbench (`/workbench`)
  3. Operations Center queues (`/ops`)
  4. AI Investigator copilot (`/investigator`)

## 3. No Mock Data in Production Invariant
- **STRICT INVARIANT**: Mock data, synthetic placeholders, or fictitious hardcoded fallbacks must **NEVER** be served in production workflows, APIs, client deliverables, or POFs.
- All pipeline stages (dockets, deeds, mortgages, skip-trace contacts, assessor data) must derive from authentic sources:
  1. Real municipal court dockets and County Auditor recordings (JIS, LINX, Odyssey, Auditor Portals, Published Legal Notices).
  2. Live database models (`ProbateCaseModel`, `OpportunityModel`, `ClientModel`).
  3. Real vendor integrations or direct scraping pipelines.
- **Fail Transparently**: When external records or vendor feeds cannot locate data for a subject parcel or fiduciary, the platform must report transparent status flags (e.g. `PENDING_RECORD_RETRIEVAL`, `TITLE_RESEARCH_IN_PROGRESS`, `NO_RECORDS_LOCATED`) rather than inventing synthetic phone numbers, imaginary deed numbers, or simulated mortgage amounts.
- Test fixtures and synthetic seed generators must be strictly isolated to the `tests/` directory and test databases, and must never contaminate production data stores or client deliverables.

## 4. No Incomplete Modules or Stubs Invariant (Production-Ready Code Only)
- **STRICT INVARIANT**: Code delivered to the codebase must be fully implemented, end-to-end wired, production-ready, and operational.
- **Zero Half-Baked Implementations**:
  - No empty or dummy endpoints returning unpopulated templates.
  - No `TODO`, `FIXME`, or `NotImplementedError` placeholders in business logic.
  - Every API endpoint must have validated request/response models, database persistence or genuine integration execution, and error handling.
  - Every frontend UI element (buttons, forms, selectors, modals, drawers) must be wired to real backend endpoints with active event listeners and robust state transitions.
- **Verification Requirement**: No feature or module is considered complete without automated tests (pytest) validating functionality and confirming 100% test pass rate with zero regressions.

## 5. Cryptographic Integrity & Fail-Closed Invariant
- **STRICT INVARIANT**: Cryptographic routines must fail closed.
- Decryption failures (e.g. Fernet / AES-256) must **NEVER** silently fall back to `base64.b64decode` or return unencrypted plaintext.
- Any ciphertext format mismatch, tampering, or key invalidation must raise an explicit `ValueError` or cryptographic exception immediately.
- Encryption keys (e.g. `AES_SECRET_KEY`) must never have hardcoded fallback strings; startup must fail fast (`RuntimeError`) if missing.

## 6. Deterministic Multi-Tenancy & Authorization Boundaries
- **Zero Default Tenancy**: Unrecognized or unmapped Clerk organization IDs must **NEVER** default to a fallback county (e.g., defaulting unknown orgs to Pierce County).
- If an organization ID is not actively mapped in `CLERK_ORG_COUNTY_MAP` or database contract records, the request must fail immediately with `HTTP_403_FORBIDDEN`.
- Production requests must authenticate via verified Clerk JWT tokens. Raw header trust (`x-clerk-*`) is strictly prohibited unless `DEMO_MODE=true` is explicitly enabled.

## 7. Ingestion Batch Transaction Isolation & Resilience
- Every batch ingestion pipeline (court dockets, auditor deeds, tax liens, obituary notices) must isolate individual item processing.
- The per-item processing loop must wrap each record in a `try/except` block with an explicit `db.rollback()` on exception.
- A single malformed docket or schema violation must be logged and quarantined without aborting or poisoning the remaining batch.

## 8. Outbound I/O Circuit Breakers & Timeout Invariants
- All outbound network calls to external LLMs (e.g., Ollama, Azure OpenAI) and third-party vendor APIs must have conservative timeouts (e.g. <= 15s) and automated circuit breakers.
- Consecutive failures (e.g., 3 failures) must trip the circuit breaker into a cooldown state (e.g., 60s) to prevent cascading thread exhaustion or worker pool starvation.
- All startup configuration keys defined in `.env.example` must be validated via `validate_environment()` upon boot, failing fast if mandatory environment variables are missing.

## 9. Modern Frontend Architecture & Security Invariant (React 18 SPA)
- The user interface is exclusively implemented as a unified React 18 + TypeScript SPA located in `frontend/`.
- **Zero Legacy Mock Apps**: Never build, maintain, or serve legacy static mock folders (`apps/*`).
- **Safe Rendering**: All dynamic data, court records, and decedent information must be rendered via standard React JSX binding (never `dangerouslySetInnerHTML`) to prevent XSS.
- **Strongly-Typed API Service**: Frontend API communication must use `frontend/src/services/api.ts` with branded ID types, strict DTO models, and `/api/v1` route endpoints.

## 10. Adversarial Audit & Backlog Verification Invariant
- **Zero Self-Certification without Adversarial Check**: Never mark an audit issue, defect, or backlog item as `[x] Remediated` or `Verified` based on a partial fix or happy-path test.
- **Exhaustive Surface Coverage**: When fixing a vulnerability pattern (e.g. DOM XSS, unauthenticated routes, missing error handling), audit and verify **every** consumer across the entire monorepo (all frontend apps and all API endpoints).
- **Dual Verification Requirement**:
  1. Automated test suite (pytest) covering the specific defect scenario and edge cases.
  2. Forensic source-code spot-check verifying all relevant files adhere to the fix.

## 11. Canonical Single-Brain Codebase Layout Invariant
- **STRICT INVARIANT**: The repository has exactly two active application directories:
  1. `backend/app/` — FastAPI API, ORM models, scoring engines, harvesters, and services.
  2. `frontend/` — Consolidated React 18 SPA (Vite + Tailwind CSS).
- **Banned Split-Brain Generations**:
  - **NEVER** re-create, maintain, or push code into `src/` or `src/gieni_os/`.
  - **NEVER** re-create or maintain legacy `apps/` mock folders.
  - Any attempt to resurrect legacy directories is an architectural regression.

## 12. Unified Server & SPA Mount Invariant
- `backend/app/main.py` is the single operational application entrypoint.
- `frontend/dist` must be served directly by FastAPI:
  - `/assets` mounts static distribution assets via `StaticFiles`.
  - `/favicon.svg` serves the brand favicon.
  - `/`, `/portal`, and `/app` serve `frontend/dist/index.html`.
- Development testing and production delivery must operate seamlessly from a single origin (`http://127.0.0.1:8000`).

## 13. Canonical 14-Stage Opportunity Lifecycle Engine (OLE) Invariant
- **Single FSM Source of Truth**: All lifecycle stages, transitions, and gate checks must strictly enforce the 14-stage OLE state machine (`backend/app/services/fsm.py` and `backend/app/models/enums.py`).
- **Banned State Machine Variants**: Competing 9-stage or 15-stage state machines are strictly prohibited.
- **Deterministic Quality Gate**: Transitions to `DELIVERED` require `is_qc_certified == True` passing all 6 deterministic gates.


