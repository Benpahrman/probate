"""
Gieni OS Knowledge Service (Subsystem 4)
Institutional memory preserving County Rules, Research SOPs,
Attorney Patterns, Title Patterns, and Authority Paths.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from gieni_os.database.models import KnowledgeArticleModel
from gieni_os.intelligence.models import KnowledgeArticleDTO


class KnowledgeService:
    """Manages verified institutional probate legal and title intelligence articles."""

    def __init__(self, db: Session):
        self.db = db
        self._ensure_seed_knowledge()

    def add_article(
        self,
        category: str,
        title: str,
        content: str,
        county_id: Optional[str] = None,
        statutory_reference: Optional[str] = None,
        version: str = "1.0.0",
    ) -> KnowledgeArticleDTO:
        """Store or update a verified institutional knowledge article."""
        article = (
            self.db.query(KnowledgeArticleModel)
            .filter(
                KnowledgeArticleModel.category == category,
                KnowledgeArticleModel.title == title,
            )
            .first()
        )

        if not article:
            article = KnowledgeArticleModel(
                category=category,
                title=title,
                content=content,
                county_id=county_id,
                statutory_reference=statutory_reference,
                version=version,
            )
            self.db.add(article)
        else:
            article.content = content
            article.county_id = county_id
            article.statutory_reference = statutory_reference
            article.version = version

        self.db.commit()
        self.db.refresh(article)
        return self._to_dto(article)

    def get_county_rules(self, county_name: str) -> List[KnowledgeArticleDTO]:
        """Fetch verified operational patterns and local rules for a county."""
        articles = (
            self.db.query(KnowledgeArticleModel)
            .filter(
                KnowledgeArticleModel.category == "COUNTY_RULES",
                KnowledgeArticleModel.title.ilike(f"%{county_name}%"),
            )
            .all()
        )
        return [self._to_dto(a) for a in articles]

    def get_statutory_sop(self, statutory_code: str) -> List[KnowledgeArticleDTO]:
        """Fetch standard operating procedures for a specific statutory code (e.g. RCW 11.68)."""
        articles = (
            self.db.query(KnowledgeArticleModel)
            .filter(
                KnowledgeArticleModel.statutory_reference.ilike(f"%{statutory_code}%")
            )
            .all()
        )
        return [self._to_dto(a) for a in articles]

    def list_articles(self, category: Optional[str] = None) -> List[KnowledgeArticleDTO]:
        """List articles optionally filtered by category."""
        q = self.db.query(KnowledgeArticleModel)
        if category:
            q = q.filter(KnowledgeArticleModel.category == category)
        return [self._to_dto(a) for a in q.all()]

    def _to_dto(self, article: KnowledgeArticleModel) -> KnowledgeArticleDTO:
        return KnowledgeArticleDTO(
            id=article.id,
            category=article.category,
            title=article.title,
            content=article.content,
            county_id=article.county_id,
            statutory_reference=article.statutory_reference,
            version=article.version,
        )

    def _ensure_seed_knowledge(self):
        """Seed foundational Washington State institutional knowledge if table is empty."""
        count = self.db.query(KnowledgeArticleModel).count()
        if count > 0:
            return

        seeds = [
            {
                "category": "COUNTY_RULES",
                "title": "Thurston County Probate Procedures",
                "county_id": "county-thurston-app",
                "statutory_reference": "LSPR 98.04",
                "content": "Thurston County Superior Court requires hearing for nonintervention powers unless solvency is established by affidavit. Average timeline for issuance of Letters Testamentary is 45 calendar days.",
            },
            {
                "category": "COUNTY_RULES",
                "title": "Pierce County LINX Probate Standards",
                "county_id": "county-pierce-app",
                "statutory_reference": "PCLR 98.04",
                "content": "Pierce County filings indexed in LINX. Nonintervention orders can be entered ex parte if will explicitly directs nonintervention. Benchmark turnaround for docket entry is 14 to 21 days.",
            },
            {
                "category": "AUTHORITY_PATTERN",
                "title": "RCW 11.68 Nonintervention Power of Sale",
                "county_id": None,
                "statutory_reference": "RCW 11.68.011",
                "content": "Under RCW 11.68.011, once an order granting nonintervention powers is recorded and letters are issued, the personal representative holds sole autonomous capacity to execute deeds, lease, and mortgage real property without judicial confirmation.",
            },
            {
                "category": "TITLE_PATTERN",
                "title": "Community Property Agreement Vesting",
                "county_id": None,
                "statutory_reference": "RCW 26.16.120",
                "content": "When recorded Community Property Agreement (CPA) is located with death certificate, title vests in surviving spouse by operation of law without requiring full probate administration.",
            },
        ]

        for s in seeds:
            record = KnowledgeArticleModel(**s)
            self.db.add(record)
        self.db.commit()
