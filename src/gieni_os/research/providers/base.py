"""
Base Research Provider Abstract Interface
Allows Gieni OS to plug in arbitrary municipal, skip-trace, title, and court research adapters.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from gieni_os.research.models import (
    ResearchArea,
    ResearchRequest,
    ProviderInfo
)

class BaseResearchProvider(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier for this provider."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Provider adapter version."""
        pass

    @property
    @abstractmethod
    def supported_areas(self) -> List[ResearchArea]:
        """List of research areas this provider can execute."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Summary of data feeds and statutory sources tapped by provider."""
        pass

    def get_info(self) -> ProviderInfo:
        return ProviderInfo(
            provider_id=self.provider_id,
            name=self.name,
            version=self.version,
            supported_areas=self.supported_areas,
            description=self.description,
            status="ACTIVE"
        )

    @abstractmethod
    def execute(self, req: ResearchRequest, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute research against the provider's data feeds.
        Returns a dictionary payload matching the expected result model.
        """
        pass
