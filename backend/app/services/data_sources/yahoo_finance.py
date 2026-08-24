import yfinance as yf
import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

from app.core.cache import cache

logger = logging.getLogger(__name__)


class YahooFinanceService:
    """Service for fetching data from Yahoo Finance."""

    def __init__(self):
        self.source = "yahoo_finance"

    async def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive stock information."""
        cache_key = cache.get_stock_cache_key(symbol, "info")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info or "symbol" not in info:
                raise ValueError(f"Stock {symbol} not found")

            result = {
                "symbol": symbol,
                "name": info.get("longName", info.get("shortName")),
                "market": info.get("market"),
                "exchange": info.get("exchange"),
                "currency": info.get("currency"),
                "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
                "previous_close": info.get("previousClose"),
                "open": info.get("open"),
                "day_high": info.get("dayHigh"),
                "day_low": info.get("dayLow"),
                "volume": info.get("volume"),
                "avg_volume": info.get("averageVolume"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "eps": info.get("trailingEps"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "description": info.get("longBusinessSummary"),
                "website": info.get("website"),
                "employees": info.get("fullTimeEmployees"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "source": self.source,
                "fetched_at": datetime.utcnow().isoformat(),
            }

            # Cache for 15 minutes
            cache.set(cache_key, result, expire=900)

            return result

        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {e}")
            raise

    async def get_historical_data(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get historical price data."""
        cache_key = cache.get_stock_cache_key(symbol, f"history_{period}_{interval}")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            ticker = yf.Ticker(symbol)

            if start and end:
                df = ticker.history(start=start, end=end, interval=interval)
            else:
                df = ticker.history(period=period, interval=interval)

            if df.empty:
                raise ValueError(f"No historical data for {symbol}")

            # Convert to list of dicts
            data = []
            for index, row in df.iterrows():
                data.append({
                    "date": index.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                    "dividends": float(row.get("Dividends", 0)),
                    "stock_splits": float(row.get("Stock Splits", 0)),
                })

            result = {
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "data": data,
                "source": self.source,
                "fetched_at": datetime.utcnow().isoformat(),
            }

            # Cache for 1 hour
            cache.set(cache_key, result, expire=3600)

            return result

        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            raise

    async def get_financials(self, symbol: str) -> Dict[str, Any]:
        """Get financial statements."""
        cache_key = cache.get_stock_cache_key(symbol, "financials")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            ticker = yf.Ticker(symbol)

            result = {
                "symbol": symbol,
                "income_statement": self._dataframe_to_dict(ticker.income_stmt),
                "balance_sheet": self._dataframe_to_dict(ticker.balance_sheet),
                "cash_flow": self._dataframe_to_dict(ticker.cashflow),
                "quarterly_income": self._dataframe_to_dict(ticker.quarterly_income_stmt),
                "quarterly_balance": self._dataframe_to_dict(ticker.quarterly_balance_sheet),
                "quarterly_cashflow": self._dataframe_to_dict(ticker.quarterly_cashflow),
                "source": self.source,
                "fetched_at": datetime.utcnow().isoformat(),
            }

            # Cache for 24 hours
            cache.set(cache_key, result, expire=86400)

            return result

        except Exception as e:
            logger.error(f"Error fetching financials for {symbol}: {e}")
            raise

    async def get_recommendations(self, symbol: str) -> Dict[str, Any]:
        """Get analyst recommendations."""
        cache_key = cache.get_stock_cache_key(symbol, "recommendations")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            ticker = yf.Ticker(symbol)

            result = {
                "symbol": symbol,
                "recommendations": self._dataframe_to_dict(ticker.recommendations),
                "upgrades_downgrades": self._dataframe_to_dict(ticker.upgrades_downgrades),
                "source": self.source,
                "fetched_at": datetime.utcnow().isoformat(),
            }

            # Cache for 24 hours
            cache.set(cache_key, result, expire=86400)

            return result

        except Exception as e:
            logger.error(f"Error fetching recommendations for {symbol}: {e}")
            raise

    def _dataframe_to_dict(self, df: Optional[pd.DataFrame]) -> Optional[List[Dict]]:
        """Convert DataFrame to list of dicts."""
        if df is None or df.empty:
            return None

        # Convert index to string
        df = df.reset_index()
        df.columns = [str(col) for col in df.columns]

        return df.to_dict(orient="records")


# Global service instance
yahoo_finance_service = YahooFinanceService()
