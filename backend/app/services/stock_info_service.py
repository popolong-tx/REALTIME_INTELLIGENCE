from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.services.data_sources.data_aggregator import data_aggregator, DataSource
from app.core.cache import cache

logger = logging.getLogger(__name__)


class StockInfoService:
    """Service for querying stock basic information."""

    async def get_stock_overview(
        self,
        symbol: str,
        preferred_source: Optional[DataSource] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive stock overview."""
        # Check cache first
        cache_key = cache.get_stock_cache_key(symbol, "overview")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            # Fetch from aggregator with failover
            result = await data_aggregator.get_stock_info(
                symbol, preferred_source
            )

            # Add computed fields
            result["price_change"] = self._calculate_price_change(
                result.get("current_price"),
                result.get("previous_close"),
            )
            result["price_change_percent"] = self._calculate_price_change_percent(
                result.get("current_price"),
                result.get("previous_close"),
            )

            # Cache for 15 minutes
            cache.set(cache_key, result, expire=900)

            return result

        except Exception as e:
            logger.error(f"Error getting stock overview for {symbol}: {e}")
            raise

    async def get_market_summary(
        self,
        symbols: List[str],
    ) -> Dict[str, Any]:
        """Get summary for multiple stocks."""
        results = []

        for symbol in symbols:
            try:
                overview = await self.get_stock_overview(symbol)
                results.append({
                    "symbol": symbol,
                    "name": overview.get("name"),
                    "current_price": overview.get("current_price"),
                    "price_change": overview.get("price_change"),
                    "price_change_percent": overview.get("price_change_percent"),
                    "volume": overview.get("volume"),
                    "market_cap": overview.get("market_cap"),
                })
            except Exception as e:
                logger.error(f"Error getting summary for {symbol}: {e}")
                results.append({
                    "symbol": symbol,
                    "error": str(e),
                })

        return {
            "stocks": results,
            "total": len(results),
            "fetched_at": datetime.utcnow().isoformat(),
        }

    async def get_price_history(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
    ) -> Dict[str, Any]:
        """Get price history for charting."""
        cache_key = cache.get_stock_cache_key(symbol, f"price_history_{period}_{interval}")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            result = await data_aggregator.get_historical_data(
                symbol, period, interval
            )

            # Format for charting
            if "data" in result:
                result["chart_data"] = {
                    "dates": [d.get("date") for d in result["data"]],
                    "prices": [d.get("close") for d in result["data"]],
                    "volumes": [d.get("volume") for d in result["data"]],
                }

            # Cache for 1 hour
            cache.set(cache_key, result, expire=3600)

            return result

        except Exception as e:
            logger.error(f"Error getting price history for {symbol}: {e}")
            raise

    async def get_financial_summary(
        self,
        symbol: str,
    ) -> Dict[str, Any]:
        """Get financial summary."""
        cache_key = cache.get_stock_cache_key(symbol, "financial_summary")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            result = await data_aggregator.get_financials(symbol)

            # Extract key metrics
            if "income_statement" in result and result["income_statement"]:
                latest = result["income_statement"][0] if result["income_statement"] else {}
                result["key_metrics"] = {
                    "revenue": latest.get("Total Revenue"),
                    "net_income": latest.get("Net Income"),
                    "gross_profit": latest.get("Gross Profit"),
                    "operating_income": latest.get("Operating Income"),
                }

            # Cache for 24 hours
            cache.set(cache_key, result, expire=86400)

            return result

        except Exception as e:
            logger.error(f"Error getting financial summary for {symbol}: {e}")
            raise

    def _calculate_price_change(
        self,
        current_price: Optional[float],
        previous_close: Optional[float],
    ) -> Optional[float]:
        """Calculate price change."""
        if current_price and previous_close:
            return round(current_price - previous_close, 2)
        return None

    def _calculate_price_change_percent(
        self,
        current_price: Optional[float],
        previous_close: Optional[float],
    ) -> Optional[float]:
        """Calculate price change percentage."""
        if current_price and previous_close and previous_close != 0:
            return round(((current_price - previous_close) / previous_close) * 100, 2)
        return None


# Global service instance
stock_info_service = StockInfoService()
