import httpx
import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.core.config import settings
from app.core.cache import cache

logger = logging.getLogger(__name__)


class AlphaVantageService:
    """Service for fetching data from Alpha Vantage API."""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self):
        self.api_key = settings.ALPHA_VANTAGE_API_KEY
        self.source = "alpha_vantage"

    async def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to Alpha Vantage API."""
        params["apikey"] = self.api_key

        async with httpx.AsyncClient() as client:
            response = await client.get(self.BASE_URL, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()

            if "Error Message" in data:
                raise ValueError(data["Error Message"])

            if "Note" in data:
                logger.warning(f"Alpha Vantage rate limit: {data['Note']}")

            return data

    async def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Get stock overview information."""
        cache_key = cache.get_stock_cache_key(symbol, "av_info")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            data = await self._make_request({
                "function": "OVERVIEW",
                "symbol": symbol,
            })

            if not data or "Symbol" not in data:
                raise ValueError(f"Stock {symbol} not found")

            result = {
                "symbol": data.get("Symbol"),
                "name": data.get("Name"),
                "description": data.get("Description"),
                "exchange": data.get("Exchange"),
                "currency": data.get("Currency"),
                "country": data.get("Country"),
                "sector": data.get("Sector"),
                "industry": data.get("Industry"),
                "market_cap": self._parse_number(data.get("MarketCapitalization")),
                "pe_ratio": self._parse_number(data.get("PERatio")),
                "peg_ratio": self._parse_number(data.get("PEGRatio")),
                "book_value": self._parse_number(data.get("BookValue")),
                "dividend_per_share": self._parse_number(data.get("DividendPerShare")),
                "dividend_yield": self._parse_number(data.get("DividendYield")),
                "eps": self._parse_number(data.get("EPS")),
                "revenue_per_share": self._parse_number(data.get("RevenuePerShareTTM")),
                "profit_margin": self._parse_number(data.get("ProfitMargin")),
                "operating_margin": self._parse_number(data.get("OperatingMarginTTM")),
                "return_on_assets": self._parse_number(data.get("ReturnOnAssetsTTM")),
                "return_on_equity": self._parse_number(data.get("ReturnOnEquityTTM")),
                "revenue": self._parse_number(data.get("RevenueTTM")),
                "gross_profit": self._parse_number(data.get("GrossProfitTTM")),
                "diluted_eps": self._parse_number(data.get("DilutedEPSTTM")),
                "quarterly_earnings_growth": self._parse_number(data.get("QuarterlyEarningsGrowthYOY")),
                "quarterly_revenue_growth": self._parse_number(data.get("QuarterlyRevenueGrowthYOY")),
                "analyst_target_price": self._parse_number(data.get("AnalystTargetPrice")),
                "trailing_pe": self._parse_number(data.get("TrailingPE")),
                "forward_pe": self._parse_number(data.get("ForwardPE")),
                "price_to_sales": self._parse_number(data.get("PriceToSalesRatioTTM")),
                "price_to_book": self._parse_number(data.get("PriceToBookRatio")),
                "ev_to_revenue": self._parse_number(data.get("EVToRevenue")),
                "ev_to_ebitda": self._parse_number(data.get("EVToEBITDA")),
                "beta": self._parse_number(data.get("Beta")),
                "fifty_two_week_high": self._parse_number(data.get("52WeekHigh")),
                "fifty_two_week_low": self._parse_number(data.get("52WeekLow")),
                "fifty_day_ma": self._parse_number(data.get("50DayMovingAverage")),
                "two_hundred_day_ma": self._parse_number(data.get("200DayMovingAverage")),
                "shares_outstanding": self._parse_number(data.get("SharesOutstanding")),
                "source": self.source,
                "fetched_at": datetime.utcnow().isoformat(),
            }

            # Cache for 1 hour
            cache.set(cache_key, result, expire=3600)

            return result

        except Exception as e:
            logger.error(f"Error fetching stock info from Alpha Vantage for {symbol}: {e}")
            raise

    async def get_intraday_data(
        self,
        symbol: str,
        interval: str = "5min",
        outputsize: str = "compact",
    ) -> Dict[str, Any]:
        """Get intraday time series data."""
        cache_key = cache.get_stock_cache_key(symbol, f"av_intraday_{interval}")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            data = await self._make_request({
                "function": "TIME_SERIES_INTRADAY",
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
            })

            time_series_key = f"Time Series ({interval})"
            if time_series_key not in data:
                raise ValueError(f"No intraday data for {symbol}")

            time_series = data[time_series_key]
            parsed_data = []

            for timestamp, values in time_series.items():
                parsed_data.append({
                    "timestamp": timestamp,
                    "open": float(values["1. open"]),
                    "high": float(values["2. high"]),
                    "low": float(values["3. low"]),
                    "close": float(values["4. close"]),
                    "volume": int(values["5. volume"]),
                })

            result = {
                "symbol": symbol,
                "interval": interval,
                "data": parsed_data,
                "source": self.source,
                "fetched_at": datetime.utcnow().isoformat(),
            }

            # Cache for 5 minutes
            cache.set(cache_key, result, expire=300)

            return result

        except Exception as e:
            logger.error(f"Error fetching intraday data from Alpha Vantage for {symbol}: {e}")
            raise

    async def get_daily_data(
        self,
        symbol: str,
        outputsize: str = "compact",
    ) -> Dict[str, Any]:
        """Get daily time series data."""
        cache_key = cache.get_stock_cache_key(symbol, "av_daily")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            data = await self._make_request({
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": outputsize,
            })

            if "Time Series (Daily)" not in data:
                raise ValueError(f"No daily data for {symbol}")

            time_series = data["Time Series (Daily)"]
            parsed_data = []

            for date, values in time_series.items():
                parsed_data.append({
                    "date": date,
                    "open": float(values["1. open"]),
                    "high": float(values["2. high"]),
                    "low": float(values["3. low"]),
                    "close": float(values["4. close"]),
                    "volume": int(values["5. volume"]),
                })

            result = {
                "symbol": symbol,
                "data": parsed_data,
                "source": self.source,
                "fetched_at": datetime.utcnow().isoformat(),
            }

            # Cache for 1 hour
            cache.set(cache_key, result, expire=3600)

            return result

        except Exception as e:
            logger.error(f"Error fetching daily data from Alpha Vantage for {symbol}: {e}")
            raise

    def _parse_number(self, value: Any) -> Optional[float]:
        """Parse number from string."""
        if value is None or value == "None" or value == "-":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


# Global service instance
alpha_vantage_service = AlphaVantageService()
