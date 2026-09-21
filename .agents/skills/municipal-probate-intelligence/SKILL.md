---
name: municipal-probate-intelligence
description: Playbook for harvesting municipal probate dockets, county auditor non-probate recordings, and orchestrating multi-domain skip-trace and title research.
---

# Municipal Probate & Non-Probate Intelligence Playbook

## 1. Municipal Ingestion Channels
Probate court dockets alone capture only ~60% of real estate transfers upon death. To achieve complete jurisdiction coverage, Gieni OS harvests 3 distinct public channels:

1. **Superior Court Formal Dockets (`SUPERIOR_COURT_DOCKET`)**:
   - Pierce County LINX portal, King County ECR, Washington Courts Odyssey JIS (Case Type 4).
   - Ingests: Case number, decedent, petitioner, attorney of record, filing date.

2. **Published Notice to Creditors (`NOTICE_TO_CREDITORS`)**:
   - Seattle Daily Journal of Commerce (King), Tacoma Daily Index (Pierce), The Olympian (Thurston).
   - Statutory Basis: RCW 11.40.020. Contains clean public text of fiduciaries and legal counsel.

3. **County Auditor Non-Probate Recordings (`AUDITOR_NON_PROBATE`)**:
   - High-equity real estate conveyances executed outside probate court:
     - **Lack of Probate Affidavits (LOPA)**: RCW 82.45.197.
     - **Transfer on Death Deeds (TODD)**: RCW 64.80.
     - **Community Property Agreements (CPA)**: RCW 26.16.120.

## 2. Pipeline Deduplication & Opportunity Lifecycle
- All harvesters pass normalized `ScrapedDocket` models to `IngestionPipeline.process_dockets()`.
- Deduplication key: `ProbateCaseModel.case_number`. Duplicate dockets are safely skipped without exception.
- New dockets auto-create an `OpportunityModel` at workflow stage `NEW` with initial priority and score, logging an immutable audit event.

## 3. Multi-Domain Research Sweep Execution
When researching an opportunity, execute across 4 extensible providers:
- **Contacts**: Query `ContactResearchProvider` for wireless/landline numbers, DNC registry scrub, heir tree, and RCW-compliant outreach script.
- **Title**: Query `TitleResearchProvider` for County Auditor deed history, APN assessed values, open deeds of trust, junior/HOA liens, and title clouds.
- **Authority**: Query `AuthorityResearchProvider` for Letters Testamentary and RCW 11.68 nonintervention powers.
- **Valuation**: Query `ValuationResearchProvider` for AVM comps, repair deductions, wholesale MAO, and net equity spread.
