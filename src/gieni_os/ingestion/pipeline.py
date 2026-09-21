"""
Gieni OS Municipal Ingestion Pipeline
Processes scraped dockets, eliminates duplicates, commits ProbateCase records,
and auto-initializes Opportunities into the 9-stage workflow engine.
"""

from typing import List
from datetime import date
from sqlalchemy.orm import Session
from gieni_os.database.models import (
    CountyModel,
    ProbateCaseModel,
    OpportunityModel,
    WorkflowAuditLogModel
)
from gieni_os.ingestion.models import (
    ScrapedDocket,
    FilingChannel,
    IngestionSummary
)

from gieni_os.workflow.engine import WorkflowStage

class IngestionPipeline:
    @classmethod
    def process_dockets(
        cls,
        db: Session,
        dockets: List[ScrapedDocket],
        operator_name: str = "Automated Ingestion Pipeline"
    ) -> IngestionSummary:
        """
        Deduplicates against existing database dockets and creates OpportunityModel records.
        Rolls back transactions atomically on error.
        """
        total_found = len(dockets)
        cases_ingested = 0
        opps_created = 0
        duplicates_skipped = 0
        ingested_sample: List[ScrapedDocket] = []

        try:
            for d in dockets:
                # 1. Ensure county exists in DB
                county = db.query(CountyModel).filter(CountyModel.id == d.county_id).first()
                if not county:
                    # Fallback to create active county if not yet initialized
                    county_name = d.county_id.replace("cty_", "").title()
                    county = CountyModel(id=d.county_id, name=county_name, state="WA", status="ACTIVE", tier="TIER_1")
                    db.add(county)
                    db.flush()

                # 2. Check deduplication by unique case_number
                existing_case = db.query(ProbateCaseModel).filter(
                    ProbateCaseModel.case_number == d.case_number
                ).first()

                if existing_case:
                    duplicates_skipped += 1
                    continue

                # 3. Create ProbateCaseModel
                new_case = ProbateCaseModel(
                    case_number=d.case_number,
                    county_id=d.county_id,
                    decedent=d.decedent,
                    filing_date=d.filing_date or date.today(),
                    status="OPEN"
                )
                db.add(new_case)
                db.flush() # Populate new_case.id

                cases_ingested += 1

                # 4. Auto-initialize Opportunity in Pipeline
                # Non-probate affidavits have autonomous power and high viability
                is_non_probate = (d.channel == FilingChannel.AUDITOR_NON_PROBATE)
                init_priority = "Priority A" if is_non_probate else "Priority B"
                init_score = 94 if is_non_probate else 88
                auth_status = (
                    "Non-Probate LOPA Confirmed (RCW 82.45.197)"
                    if is_non_probate
                    else "Tier 1: Letters Pending Court Verification"
                )

                new_opp = OpportunityModel(
                    case_id=new_case.id,
                    county_id=d.county_id,
                    workflow_stage="NEW",
                    priority=init_priority,
                    authority_status=auth_status,
                    score=init_score
                )
                db.add(new_opp)
                db.flush()

                opps_created += 1

                # 5. Audit Log Entry
                audit = WorkflowAuditLogModel(
                    opportunity_id=new_opp.id,
                    from_stage=WorkflowStage.INGESTED.value,
                    to_stage=WorkflowStage.NEW.value,
                    transitioned_by=operator_name,
                    notes=(
                        f"Ingested via {d.channel.value}. "
                        f"Petitioner: {d.petitioner_name or 'N/A'} ({d.petitioner_relationship or 'N/A'}). "
                        f"Real Property: {d.property_hint or 'Schedule Attached'}."
                    )
                )
                db.add(audit)
                ingested_sample.append(d)

            db.commit()
        except Exception:
            db.rollback()
            raise

        sample_channel = dockets[0].channel.value if dockets else "MIXED_CHANNELS"
        sample_county = dockets[0].county_id if dockets else "ALL"

        return IngestionSummary(
            channel=sample_channel,
            county_id=sample_county,
            total_found=total_found,
            cases_ingested=cases_ingested,
            opportunities_created=opps_created,
            duplicates_skipped=duplicates_skipped,
            sample_dockets=ingested_sample[:5]
        )
