from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

from app.services.data_sources.data_aggregator import data_aggregator, DataSource
from app.core.cache import cache

logger = logging.getLogger(__name__)


class HistoricalDataService:
    """Service for querying historical data with timestamps and source tracking."""

    async def get_historical_prices(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "1y",
        interval: str = "1d",
        preferred_source: Optional[DataSource] = None,
    ) -> Dict[str, Any]:
        """Get historical price data with source tracking."""
        # Check cache
        cache_key = cache.get_stock_cache_key(
            symbol,
            f"historical_{period}_{interval}_{start_date}_{end_date}",
        )
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            # Fetch from aggregator
            result = await data_aggregator.get_historical_data(
                symbol, period, interval, preferred_source
            )

            # Add metadata
            result["query_params"] = {
                "symbol": symbol,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "period": period,
                "interval": interval,
            }

            # Filter by date range if specified
            if start_date or end_date:
                result["data"] = self._filter_by_date_range(
                    result.get("data", []),
                    start_date,
                    end_date,
                )

            # Add data quality metrics
            result["data_quality"] = self._calculate_data_quality(result.get("data", []))

            # Cache for 1 hour
            cache.set(cache_key, result, expire=3600)

            return result

        except Exception as e:
            logger.error(f"Error getting historical prices for {symbol}: {e}")
            raise

    async def get_daily_ohlcv(
        self,
        symbol: str,
        days: int = 365,
        preferred_source: Optional[DataSource] = None,
    ) -> Dict[str, Any]:
        """Get daily OHLCV data."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        return await self.get_historical_prices(
            symbol,
            start_date=start_date,
            end_date=end_date,
            period="1y",
            interval="1d",
            preferred_source=preferred_source,
        )

    async def get_weekly_ohlcv(
        self,
        symbol: str,
        weeks: int = 52,
        preferred_source: Optional[DataSource] = None,
    ) -> Dict[str, Any]:
        """Get weekly OHLCV data."""
        return await self.get_historical_prices(
            symbol,
            period=f"{weeks}wk",
            interval="1wk",
            preferred_source=preferred_source,
        )

    async def get_monthly_ohlcv(
        self,
        symbol: str,
        months: int = 12,
        preferred_source: Optional[DataSource] = None,
    ) -> Dict[str, Any]:
        """Get monthly OHLCV data."""
        return await self.get_historical_prices(
            symbol,
            period=f"{months}mo",
            interval="1mo",
            preferred_source=preferred_source,
        )

    async def get_intraday_data(
        self,
        symbol: str,
        interval: str = "5min",
        days: int = 5,
        preferred_source: Optional[DataSource] = None,
    ) -> Dict[str, Any]:
        """Get intraday data."""
        cache_key = cache.get_stock_cache_key(symbol, f"intraday_{interval}_{days}")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            # For intraday, we need to use specific date ranges
            # Alpha Vantage has better intraday support
            result = await data_aggregator._fetch_with_failover(
                "get_intraday_data",
                symbol,
                DataSource.ALPHA_VANTAGE,
                interval=interval,
            )

            # Add metadata
            result["query_params"] = {
                "symbol": symbol,
                "interval": interval,
                "days": days,
            }

            # Cache for 5 minutes
            cache.set(cache_key, result, expire=300)

            return result

        except Exception as e:
            logger.error(f"Error getting intraday data for {symbol}: {e}")
            raise

    def _filter_by_date_range(
        self,
        data: List[Dict[str, Any]],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> List[Dict[str, Any]]:
        """Filter data by date range."""
        filtered = []

        for item in data:
            date_str = item.get("date") or item.get("timestamp")
            if not date_str:
                continue

            try:
                if "T" in str(date_str):
                    item_date = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
                else:
                    item_date = datetime.strptime(str(date_str), "%Y-%m-%d")

                if start_date and item_date < start_date:
                    continue
                if end_date and item_date > end_date:
                    continue

                filtered.append(item)
            except (ValueError, TypeError):
                continue

        return filtered

    def _calculate_data_quality(
        self,
        data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate data quality metrics."""
        if not data:
            return {
                "total_points": 0,
                "has_gaps": False,
                "completeness": 0,
            }

        total_points = len(data)
        missing_values = 0

        for item in data:
            for key in ["open", "high", "low", "close", "volume"]:
                if item.get(key) is None:
                    missing_values += 1

        expected_values = total_points * 5  # 5 fields per data point
        completeness = (expected_values - missing_values) / expected_values if expected_values > 0 else 0

        # Check for date gaps
        has_gaps = False
        if total_points > 1:
            dates = []
            for item in data:
                date_str = item.get("date") or item.get("timestamp")
                if date_str:
                    try:
                        if "T" in str(date_str):
                            dates.append(datetime.fromisoformat(str(date_str).replace("Z", "+00:00")))
                        else:
                            dates.append(datetime.strptime(str(date_str), "%Y-%m-%d"))
                    except (ValueError, TypeError):
                        continue

            if len(dates) > 1:
                dates.sort()
                for i in range(1, len(dates)):
                    diff = (dates[i] - dates[i - 1]).days
                    if diff > 5:  # More than 5 days gap
                        has_gaps = True
                        break

        return {
            "total_points": total_points,
            "missing_values": missing_values,
            "completeness": round(completeness * 100, 2),
            "has_gaps": has_gaps,
            "date_range": {
                "start": data[0].get("date") or data[0].get("timestamp") if data else None,
                "end": data[-1].get("date") or data[-1].get("timestamp") if data else None,
            },
        }


# Global service instance
historical_data_service = HistoricalDataService()
