"""
Gieni OS Memory Service (Subsystem 1)
Persists and retrieves experiential memory across Cases, Opportunities,
Counties, Organizations, and the overall Platform.
"""

import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from gieni_os.database.models import MemoryEntryModel, MemoryObservationModel
from gieni_os.intelligence.models import (
    MemoryScope,
    ObservationSource,
    MemoryEntryDTO,
    MemoryObservationDTO,
)


class MemoryService:
    """Manages multi-scope episodic and contextual memory."""

    def __init__(self, db: Session):
        self.db = db

    def store(
        self,
        scope: MemoryScope,
        entity_id: str,
        summary: str,
        observations: Optional[List[str]] = None,
        attributes: Optional[Dict[str, Any]] = None,
        confidence: float = 0.90,
        source: ObservationSource = ObservationSource.ENGINE,
    ) -> MemoryEntryDTO:
        """Store or update an active memory entry for an entity."""
        entry = (
            self.db.query(MemoryEntryModel)
            .filter(
                MemoryEntryModel.scope == scope.value,
                MemoryEntryModel.entity_id == entity_id,
            )
            .first()
        )

        meta_str = json.dumps(attributes or {}, default=str)

        if not entry:
            entry = MemoryEntryModel(
                scope=scope.value,
                entity_id=entity_id,
                summary=summary,
                confidence=confidence,
                meta_json=meta_str,
            )
            self.db.add(entry)
            self.db.flush()
        else:
            entry.summary = summary
            entry.confidence = confidence
            if attributes:
                existing_meta = json.loads(entry.meta_json or "{}")
                existing_meta.update(attributes)
                entry.meta_json = json.dumps(existing_meta, default=str)

        if observations:
            for obs_text in observations:
                obs_record = MemoryObservationModel(
                    entry_id=entry.id,
                    observation=obs_text,
                    source=source.value,
                    confidence=confidence,
                )
                self.db.add(obs_record)

        self.db.commit()
        self.db.refresh(entry)
        return self._to_dto(entry)

    def retrieve(self, scope: MemoryScope, entity_id: str) -> Optional[MemoryEntryDTO]:
        """Fetch the consolidated memory and observations for an entity."""
        entry = (
            self.db.query(MemoryEntryModel)
            .filter(
                MemoryEntryModel.scope == scope.value,
                MemoryEntryModel.entity_id == entity_id,
            )
            .first()
        )
        if not entry:
            return None
        return self._to_dto(entry)

    def search(
        self,
        query: str,
        scope: Optional[MemoryScope] = None,
        limit: int = 10,
    ) -> List[MemoryEntryDTO]:
        """Search memory entries by keyword in summary or attributes."""
        q = self.db.query(MemoryEntryModel)
        if scope:
            q = q.filter(MemoryEntryModel.scope == scope.value)
        if query:
            q = q.filter(MemoryEntryModel.summary.ilike(f"%{query}%"))
        results = q.order_by(MemoryEntryModel.updated_at.desc()).limit(limit).all()
        return [self._to_dto(r) for r in results]

    def merge(
        self,
        scope: MemoryScope,
        entity_id: str,
        new_observations: List[str],
        summary_update: Optional[str] = None,
        confidence_delta: float = 0.0,
        source: ObservationSource = ObservationSource.AGENT,
    ) -> MemoryEntryDTO:
        """Incrementally append new observations and update confidence."""
        entry = (
            self.db.query(MemoryEntryModel)
            .filter(
                MemoryEntryModel.scope == scope.value,
                MemoryEntryModel.entity_id == entity_id,
            )
            .first()
        )
        if not entry:
            return self.store(
                scope=scope,
                entity_id=entity_id,
                summary=summary_update or "Initial consolidated memory entry.",
                observations=new_observations,
                confidence=min(1.0, max(0.1, 0.90 + confidence_delta)),
                source=source,
            )

        if summary_update:
            entry.summary = summary_update
        if confidence_delta != 0.0:
            entry.confidence = min(1.0, max(0.1, entry.confidence + confidence_delta))

        for obs in new_observations:
            obs_record = MemoryObservationModel(
                entry_id=entry.id,
                observation=obs,
                source=source.value,
                confidence=entry.confidence,
            )
            self.db.add(obs_record)

        self.db.commit()
        self.db.refresh(entry)
        return self._to_dto(entry)

    def _to_dto(self, entry: MemoryEntryModel) -> MemoryEntryDTO:
        obs_dtos = [
            MemoryObservationDTO(
                id=o.id,
                observation=o.observation,
                source=ObservationSource(o.source) if o.source in ObservationSource._value2member_map_ else ObservationSource.ENGINE,
                confidence=o.confidence,
                created_at=o.created_at,
            )
            for o in entry.observations
        ]
        attrs = json.loads(entry.meta_json or "{}")
        return MemoryEntryDTO(
            id=entry.id,
            scope=MemoryScope(entry.scope),
            entity_id=entry.entity_id,
            summary=entry.summary,
            confidence=entry.confidence,
            attributes=attrs,
            observations=obs_dtos,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )
