import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from app.services.data_sources.yahoo_finance import yahoo_finance_service
from app.services.data_sources.alpha_vantage import alpha_vantage_service
from app.services.data_sources.twelve_data import twelve_data_service
from app.core.config import settings
from app.core.cache import cache

logger = logging.getLogger(__name__)


class DataSource(str, Enum):
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    TWELVE_DATA = "twelve_data"


class DataAggregator:
    """Aggregator for multiple data sources with failover."""

    def __init__(self):
        self.sources = {
            DataSource.YAHOO_FINANCE: yahoo_finance_service,
            DataSource.ALPHA_VANTAGE: alpha_vantage_service,
            DataSource.TWELVE_DATA: twelve_data_service,
        }
        self.primary_source = DataSource.YAHOO_FINANCE
        self.source_status: Dict[DataSource, bool] = {
            DataSource.YAHOO_FINANCE: settings.YAHOO_FINANCE_ENABLED,
            DataSource.ALPHA_VANTAGE: bool(settings.ALPHA_VANTAGE_API_KEY),
            DataSource.TWELVE_DATA: twelve_data_service.configured,
        }
        self.last_error: Dict[DataSource, Optional[str]] = {
            source: None for source in DataSource
        }

    async def get_stock_info(
        self,
        symbol: str,
        preferred_source: Optional[DataSource] = None,
    ) -> Dict[str, Any]:
        """Get stock info with failover."""
        return await self._fetch_with_failover(
            "get_stock_info",
            symbol,
            preferred_source,
        )

    async def get_historical_data(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        preferred_source: Optional[DataSource] = None,
    ) -> Dict[str, Any]:
        """Get historical data with failover."""
        return await self._fetch_with_failover(
            "get_historical_data",
            symbol,
            preferred_source,
            period=period,
            interval=interval,
        )

    async def get_financials(
        self,
        symbol: str,
        preferred_source: Optional[DataSource] = None,
    ) -> Dict[str, Any]:
        """Get financial data with failover."""
        return await self._fetch_with_failover(
            "get_financials",
            symbol,
            preferred_source,
        )

    async def _fetch_with_failover(
        self,
        method: str,
        symbol: str,
        preferred_source: Optional[DataSource] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Fetch data with automatic failover."""
        # Determine source order
        sources = self._get_source_order(preferred_source)

        last_error = None

        for source in sources:
            if not self.source_status.get(source, False):
                logger.warning(f"Skipping unhealthy source: {source}")
                continue

            try:
                service = self.sources[source]
                fetch_method = getattr(service, method)

                # Add source metadata to result
                result = await fetch_method(symbol, **kwargs)
                result["data_source"] = source.value
                result["failover_used"] = source != sources[0]

                # Mark source as healthy
                self.source_status[source] = True
                self.last_error[source] = None

                return result

            except Exception as e:
                last_error = str(e)
                self.last_error[source] = last_error
                logger.error(f"Error fetching from {source}: {last_error}")

                # Mark source as unhealthy after consecutive failures
                self.source_status[source] = False

                continue

        # All sources failed
        raise Exception(f"All data sources failed for {symbol}: {last_error}")

    def _get_source_order(
        self,
        preferred_source: Optional[DataSource] = None,
    ) -> List[DataSource]:
        """Get ordered list of sources to try."""
        sources = []

        # Add preferred source first
        if preferred_source and preferred_source in self.sources:
            sources.append(preferred_source)

        # Add primary source
        if self.primary_source not in sources:
            sources.append(self.primary_source)

        # Add remaining sources
        for source in self.sources:
            if source not in sources:
                sources.append(source)

        return sources

    def get_source_status(self) -> Dict[str, Any]:
        """Get status of all data sources."""
        return {
            source.value: {
                "healthy": self.source_status.get(source, False),
                "configured": self._source_configured(source),
                "last_error": self.last_error.get(source),
            }
            for source in DataSource
        }

    def reset_source_status(self, source: DataSource) -> None:
        """Reset status of a data source."""
        self.source_status[source] = self._source_configured(source)
        self.last_error[source] = None

    def set_primary_source(self, source: DataSource) -> None:
        """Set primary data source."""
        if source in self.sources:
            self.primary_source = source

    def _source_configured(self, source: DataSource) -> bool:
        if source == DataSource.YAHOO_FINANCE:
            return settings.YAHOO_FINANCE_ENABLED
        if source == DataSource.ALPHA_VANTAGE:
            return bool(settings.ALPHA_VANTAGE_API_KEY)
        if source == DataSource.TWELVE_DATA:
            return twelve_data_service.configured
        return False


# Global aggregator instance
data_aggregator = DataAggregator()
