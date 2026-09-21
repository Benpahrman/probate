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

## 9. Frontend DOM & Template Injection Defense Invariant (Zero Raw `innerHTML`)
- In all vanilla JS applications (`apps/workbench`, `apps/dashboard`, `apps/ops-center`, `apps/client-portal`):
  1. **Strict HTML Escaping**: Any API data, database record, or model property interpolated into `innerHTML` template literals **MUST** be processed through an `escapeHTML()` helper before insertion.
  2. **Free-Text Sanitization**: User-editable freeform text (e.g. `notes`, `comments`, `log_entries`) must never be inserted without explicit HTML entity encoding.
  3. **No String Interpolation in Inline Handlers**: Never interpolate dynamic string variables (e.g., addresses or names that may contain single quotes or special characters) into inline `onclick="...('${val}')"` attributes. Always pass sanitized IDs or bind listeners programmatically using state lookup.
  4. **Institutional Server HTML**: Server-side generated HTML reports (e.g. `POF Institutional Dossiers`) must wrap all interpolated data fields using Python's `html.escape()`.

## 10. Adversarial Audit & Backlog Verification Invariant
- **Zero Self-Certification without Adversarial Check**: Never mark an audit issue, defect, or backlog item as `[x] Remediated` or `Verified` based on a partial fix or happy-path test.
- **Exhaustive Surface Coverage**: When fixing a vulnerability pattern (e.g. DOM XSS, unauthenticated routes, missing error handling), audit and verify **every** consumer across the entire monorepo (all frontend apps and all API endpoints).
- **Dual Verification Requirement**:
  1. Automated test suite (pytest) covering the specific defect scenario and edge cases.
  2. Forensic source-code spot-check verifying all relevant files adhere to the fix.

