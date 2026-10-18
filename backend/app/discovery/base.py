from abc import ABC, abstractmethod
from typing import List
from backend.app.discovery.models import (
    DiscoverySearchParams,
    DiscoveryResultItem,
    ProviderConfigStatus
)

class BaseDiscoveryProvider(ABC):
    """
    Abstract base class for all business discovery providers.
    Ensures provider independence, common configuration inspection,
    search parameter validation, execution, and normalized output.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique provider identifier (e.g. 'osm', 'google_places', 'csv')"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human readable provider name"""
        pass

    @property
    @abstractmethod
    def attribution(self) -> str:
        """Attribution text required by provider terms"""
        pass

    @property
    @abstractmethod
    def data_retention_policy(self) -> str:
        """Data retention rules for this provider (e.g. transient vs persistent)"""
        pass

    @abstractmethod
    def get_configuration_status(self) -> ProviderConfigStatus:
        """Inspects credentials, endpoint availability, and returns provider status"""
        pass

    @abstractmethod
    def validate_search_params(self, params: DiscoverySearchParams) -> None:
        """Validates provider-specific constraints (raises ValueError or HTTPException on error)"""
        pass

    @abstractmethod
    async def search(self, params: DiscoverySearchParams) -> List[DiscoveryResultItem]:
        """
        Executes business search against the provider.
        Returns normalized DiscoveryResultItem objects.
        Transient results are separate from persisted prospects.
        """
        pass
