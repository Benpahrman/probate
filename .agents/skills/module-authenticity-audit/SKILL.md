---
name: module-authenticity-audit
description: Forensic module-by-module audit playbook assessing Completeness, Business Usefulness, Simulated vs Real-World Authenticity (synthetic mocks vs live I/O), and System Necessity, providing concrete step-by-step Realization Blueprints to turn simulated code into production-grade reality.
---

# Module Authenticity, Completeness & Realization Audit Playbook

Use this skill to conduct an uncompromising, forensic audit of any module, service, provider, or engine in the codebase. Every module is evaluated across **4 mandatory dimensions**:
1. **Completeness**: Is the contract fully implemented, robustly typed, and resilient to real-world edge cases?
2. **Usefulness**: Does it solve an essential business/operational need in the production lifecycle, or is it vanity bloat/orphaned code?
3. **Simulated vs. Real-World Authenticity**: Does it rely on synthetic mocks, hardcoded fallbacks, fake entities, or hash math versus authentic I/O, external APIs, and verified database state?
4. **System Necessity & Realization Blueprint**: Is it actually needed? If yes, what is the exact step-by-step technical blueprint (external APIs, schemas, adapters, persistence) to make it real?

---

## The 4 Audit Dimensions

```
┌────────────────────────────────────────────────────────────────────────┐
│                      MODULE FORENSIC AUDIT MATRIX                      │
├──────────────────────────┬─────────────────────────────────────────────┤
│ 1. Completeness          │ Interfaces, lifecycle, error paths, types   │
│ 2. Usefulness            │ Core pipeline value, active wiring, utility │
│ 3. Authenticity (Sim vs) │ Mocks, synthetic entities, real I/O, APIs   │
│ 4. Realization Blueprint │ Verdict, target APIs, drop-in architecture  │
└──────────────────────────┴─────────────────────────────────────────────┘
```

### 1. Completeness
Audit whether the module is production-complete or an incomplete prototype:
- **Contract & Interface Fulfillment**: Does the module implement all abstract methods and protocols? Are there dangling `NotImplementedError`, `pass` placeholders, or unhandled branches?
- **Lifecycle & Edge Cases**: Are network timeouts, socket disconnects, rate limits, non-200 HTTP responses, partial payloads, and malformed inputs explicitly handled?
- **Typing & Validation**: Are inputs and outputs strictly validated via Pydantic or typed dataclasses? Are there loose untyped dicts or implicit keys?
- **Test Integrity**: Are unit tests testing real behavior, or do they pass vacuously because of short-circuits like `PYTEST_CURRENT_TEST`?

### 2. Business Usefulness & System Wiring
Audit whether the module serves a genuine, active purpose:
- **Active Lifecycle Integration**: Is the module actively imported and invoked by HTTP routes, worker queues (Celery/Temporal), or pipeline orchestrators?
- **Orphan / Zombie Code Detection**: If nothing imports or triggers this module in production workflows, flag it immediately as orphaned.
- **Value Density**: Does it provide actionable intelligence (e.g. verified skip-traced mobile numbers, auditor deed chains, statutory authority powers) or cosmetic vanity metrics?
- **Simplicity vs. Over-engineering**: Does it introduce unnecessary multi-layer abstraction indirection for a simple 10-line operation?

### 3. Simulated vs. Real-World Authenticity (The Ground Truth Test)
Audit against the workspace **Rule §4 ("Stop Doing This" List)**:
- **Zero Synthetic Entities**:
  - ❌ Never ingest fictional names (e.g., "Thomas Vance", "Theo Vance", "John Doe").
  - ❌ Never generate synthetic warranty deeds, fake loan numbers, or fake lenders (e.g., JPMorgan Chase placeholders).
  - ❌ Never generate dummy phone numbers (e.g., `(206) 555-0100`) or fake email addresses.
  - ✅ If data is missing or unindexed, represent it honestly as `None`, `404 Not Found`, or statutory `NO_RECORDS_LOCATED`.
- **Zero Modulo Math & Fake Scores**:
  - ❌ Do not calculate fake equity, scores, or probabilities using `hash(name) % 100` or random generators.
  - ✅ Use empirical metrics: assessed county value, real deed deed-of-trust amounts, actual recorded liens.
- **Zero Fake Deliveries**:
  - ❌ Never return `status="SUCCESS"` or `200 OK` unless an authentic HTTP payload was transmitted over the wire and acknowledged by the target webhook/endpoint.
- **I/O Authenticity**:
  - Does the module make genuine outbound HTTP/gRPC/SQL/Graph calls?
  - Or does it silently return hardcoded in-memory dictionaries pretending to be live data?

### 4. System Necessity & The Realization Blueprint
Make a definitive architectural verdict and prescribe the exact transformation:
- **Verdict Options**:
  - `KEEP_AND_HARDEN`: Essential module that is already real or nearly real; harden error handling, types, and tests.
  - `MAKE_REAL`: Essential business capability currently faked or simulated; requires live external APIs and storage.
  - `MERGE`: Redundant capability; consolidate into an existing primary service to cut architectural sprawl.
  - `DEPRECATE_AND_PURGE`: Non-essential, cosmetic, or orphaned module; delete to eliminate maintenance liability.
- **If `MAKE_REAL` or `KEEP_AND_HARDEN` — The Realization Blueprint**:
  1. **Official Data Sources / APIs**: Identify the exact live API, court portal, county auditor system, or vendor (e.g., Pierce County LINX, King County ECR, ATTOM Data, LexisNexis, BatchData, GovSpend, ClerkRecorder).
  2. **Authentication & Environment Configuration**: Exact environment variables required (e.g., `COUNTY_API_KEY`, `SKIP_TRACE_TOKEN`).
  3. **I/O Client Architecture**: Drop-in HTTP client implementation with connection pooling (`httpx.AsyncClient`), retry/backoff policy (Tenacity), and rate limiting.
  4. **Data Schema & Models**: Pydantic models for raw API responses and normalized domain models.
  5. **Persistence & Graph Wiring**: Database schema migrations or Neo4j relationship updates needed to store the authentic ground truth.
  6. **Concrete Code Recipe**: Provide production-ready, drop-in replacement code.

---

## Step-by-Step Audit Execution Workflow

When tasked with auditing a module or set of modules, follow this sequence:

### Step 1: Static Code Inspection & Import Graph Trace
1. Inspect the target file using `view_file`.
2. Trace incoming imports using `grep_search` to verify if and where the module is invoked across the codebase:
   ```bash
   grep_search: Query="from ... import TargetClass" or "import TargetModule"
   ```
3. Check for synthetic signatures:
   - Search for `555-`, `vance`, `dummy`, `mock`, `fake`, `random`, `sample`, `hash(` in the file.

### Step 2: Evaluate the 4 Lenses
Grade each dimension on a scale of 0 to 100%:
- **Completeness Score** (0-100%)
- **Usefulness Score** (0-100%)
- **Authenticity Score** (0-100%)
- **Overall Readiness Grade**: `A` (90-100%), `B` (80-89%), `C` (70-79%), `D` (60-69%), `F` (<60%)

### Step 3: Formulate the Realization Blueprint
If the module is simulated or partially stubbed:
- Detail the exact third-party API or municipal portal needed.
- Write the concrete adapter code replacing mocks with live `httpx` or database queries.
- Specify how missing data is safely handled (`None` / `NO_RECORDS_LOCATED`).

### Step 4: Generate the Standardized Audit Report
Output the audit in the standardized markdown format below.

---

## Standardized Module Audit Report Format

When executing this skill, output the report using this structure:

```markdown
# Module Forensic Audit: `path/to/module.py`

## Executive Summary
- **Module Name**: `module_name`
- **Primary Responsibility**: Brief description of purpose.
- **Verdict**: [ KEEP_AND_HARDEN | MAKE_REAL | MERGE | DEPRECATE_AND_PURGE ]
- **Overall Grade**: [ A / B / C / D / F ]

### Scorecard
| Dimension | Score | Status | Key Observation |
|---|:---:|:---:|---|
| **Completeness** | XX% | [Pass / Warn / Fail] | Summary of contract, types, and error handling |
| **Usefulness** | XX% | [Pass / Warn / Fail] | Summary of pipeline integration and business value |
| **Authenticity** | XX% | [Pass / Warn / Fail] | Live I/O vs. synthetic fallbacks / mocks |
| **Overall Authenticity** | XX% | [Grade] | Ready for production vs needs remediation |

---

## Detailed Audit Findings

### 1. Completeness & Edge Cases
- **Contract Fulfillment**: [Detailed breakdown]
- **Error Handling & Timeouts**: [Detailed breakdown]
- **Test Coverage**: [Existing test assessment]

### 2. Business Usefulness & System Role
- **Pipeline Role**: [Where does it fit in the ingestion/decision/delivery lifecycle?]
- **Callers & Call Sites**: [List files importing and calling this module]
- **Orphan Status**: [Active / Orphaned / Redundant]

### 3. Simulated vs. Real-World Use (Ground Truth Analysis)
- **Synthetic Data & Fallbacks Detected**: [List any fake names, deeds, phones, or hashes]
- **Live I/O Verification**: [Are network and database operations genuine?]
- **Rule §4 Compliance**: [Pass / Fail with specific line references]

---

## Realization Blueprint: How to Make It Real

### Target External Sources & Endpoints
- **Provider / Municipal Authority**: [e.g., King County Auditor, Pierce County LINX, ATTOM API]
- **Authentication**: [Required env vars and auth scheme]
- **Rate Limits & SLAs**: [Throttling considerations]

### Architecture & Adapter Design
- **HTTP Client / DB Connector**: [AsyncClient, connection pool, retry policies]
- **Data Contract / Pydantic Schema**: [Input / Output schemas]
- **Persistence Updates**: [DB columns, indices, or Neo4j node/edges needed]

### Drop-in Production Code Replacement
```python
# Concrete, production-grade drop-in code replacing any simulation
```

---

## Prioritized Action Plan
1. **[P0 / Immediate]**: Critical fixes (remove synthetic data, add authentic network call).
2. **[P1 / Next]**: Integration & contract hardening (Pydantic validation, error retries).
3. **[P2 / Polish]**: Telemetry, caching, and end-to-end integration tests.
```
