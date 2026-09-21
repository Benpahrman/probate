"""
Gieni OS Learning Service (Subsystem 5)
Converts downstream transaction outcomes (Offers, Contracts, Dead Deals, No Responses)
into calibrated operational intelligence, county friction updates, and score recalibrations.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from gieni_os.database.models import (
    LearningEventModel,
    CountyCalibrationModel,
    OpportunityModel,
)
from gieni_os.intelligence.models import (
    LearningOutcomeType,
    LearningEventDTO,
)


class LearningService:
    """Manages continuous feedback loops and heuristic recalibration."""

    def __init__(self, db: Session):
        self.db = db
        self._ensure_seed_calibrations()

    def record_outcome(
        self,
        opportunity_id: str,
        county_id: str,
        event_type: LearningOutcomeType,
        realized_margin: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> LearningEventDTO:
        """Log a real-world deal outcome and trigger adaptive weight adjustments."""
        # Calculate dynamic score impact based on transaction feedback
        delta_score = 0.0
        if event_type == LearningOutcomeType.CLOSING:
            delta_score = +5.0
        elif event_type == LearningOutcomeType.CONTRACT:
            delta_score = +3.0
        elif event_type == LearningOutcomeType.OFFER:
            delta_score = +1.0
        elif event_type == LearningOutcomeType.DEAD_DEAL:
            delta_score = -4.0
        elif event_type == LearningOutcomeType.NO_RESPONSE:
            delta_score = -1.5

        event = LearningEventModel(
            opportunity_id=opportunity_id,
            county_id=county_id,
            event_type=event_type.value,
            realized_margin=realized_margin,
            delta_score=delta_score,
            notes=notes,
        )
        self.db.add(event)

        # Update Opportunity score if opportunity exists
        opp = self.db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
        if opp:
            opp.score = max(0, min(100, int(opp.score + delta_score)))

        # Update county friction index on deal termination
        if event_type == LearningOutcomeType.DEAD_DEAL:
            self._adjust_county_friction(county_id, delta=0.05)
        elif event_type == LearningOutcomeType.CLOSING:
            self._adjust_county_friction(county_id, delta=-0.05)

        self.db.commit()
        self.db.refresh(event)
        return self._to_dto(event)

    def get_county_friction(self, county_name: str) -> float:
        """Retrieve the dynamic friction index for a county (1.0 = baseline)."""
        record = (
            self.db.query(CountyCalibrationModel)
            .filter(CountyCalibrationModel.county_name.ilike(f"%{county_name}%"))
            .first()
        )
        if not record:
            return 1.0
        return record.friction_index

    def recalibrate_county(
        self,
        county_name: str,
        friction_index: float,
        avg_docket_days: int = 45,
        nonintervention_rate: float = 0.85,
    ) -> CountyCalibrationModel:
        """Update calibration constants for a jurisdiction."""
        record = (
            self.db.query(CountyCalibrationModel)
            .filter(CountyCalibrationModel.county_name.ilike(f"%{county_name}%"))
            .first()
        )
        if not record:
            record = CountyCalibrationModel(
                county_name=county_name,
                friction_index=friction_index,
                avg_docket_days=avg_docket_days,
                nonintervention_rate=nonintervention_rate,
            )
            self.db.add(record)
        else:
            record.friction_index = friction_index
            record.avg_docket_days = avg_docket_days
            record.nonintervention_rate = nonintervention_rate

        self.db.commit()
        self.db.refresh(record)
        return record

    def get_learning_history(
        self,
        opportunity_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[LearningEventDTO]:
        q = self.db.query(LearningEventModel)
        if opportunity_id:
            q = q.filter(LearningEventModel.opportunity_id == opportunity_id)
        results = q.order_by(LearningEventModel.created_at.desc()).limit(limit).all()
        return [self._to_dto(e) for e in results]

    def _adjust_county_friction(self, county_id: str, delta: float):
        record = (
            self.db.query(CountyCalibrationModel)
            .filter(CountyCalibrationModel.id == county_id)
            .first()
        )
        if record:
            record.friction_index = max(0.5, min(2.5, record.friction_index + delta))

    def _to_dto(self, event: LearningEventModel) -> LearningEventDTO:
        return LearningEventDTO(
            id=event.id,
            opportunity_id=event.opportunity_id,
            county_id=event.county_id,
            event_type=LearningOutcomeType(event.event_type),
            realized_margin=event.realized_margin,
            delta_score=event.delta_score,
            notes=event.notes,
            created_at=event.created_at,
        )

    def _ensure_seed_calibrations(self):
        count = self.db.query(CountyCalibrationModel).count()
        if count > 0:
            return

        defaults = [
            {"county_name": "Pierce", "friction_index": 1.05, "avg_docket_days": 35, "nonintervention_rate": 0.88},
            {"county_name": "Thurston", "friction_index": 1.20, "avg_docket_days": 45, "nonintervention_rate": 0.81},
            {"county_name": "King", "friction_index": 1.45, "avg_docket_days": 60, "nonintervention_rate": 0.74},
            {"county_name": "Snohomish", "friction_index": 1.15, "avg_docket_days": 40, "nonintervention_rate": 0.84},
            {"county_name": "Clark", "friction_index": 1.10, "avg_docket_days": 38, "nonintervention_rate": 0.86},
        ]
        for d in defaults:
            self.db.add(CountyCalibrationModel(**d))
        self.db.commit()
