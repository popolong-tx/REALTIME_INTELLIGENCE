import re
from typing import Optional, List, Dict, Any
import yfinance as yf
from datetime import datetime

from app.core.cache import cache


class StockValidator:
    """Service for validating stock codes."""

    # Common stock code patterns
    PATTERNS = {
        "US": r"^[A-Z]{1,5}$",
        "HK": r"^\d{1,5}\.HK$",
        "SH": r"^\d{6}\.SH$",
        "SZ": r"^\d{6}\.SZ$",
        "JP": r"^\d{4}\.T$",
    }

    # Common stock exchanges
    EXCHANGES = {
        "US": ["NYSE", "NASDAQ", "AMEX"],
        "HK": ["HKEX"],
        "SH": ["SSE"],
        "SZ": ["SZSE"],
        "JP": ["TSE"],
    }

    def validate_format(self, symbol: str) -> bool:
        """Validate stock code format."""
        symbol = symbol.strip().upper()

        for market, pattern in self.PATTERNS.items():
            if re.match(pattern, symbol):
                return True

        return False

    def get_market(self, symbol: str) -> Optional[str]:
        """Get market for stock code."""
        symbol = symbol.strip().upper()

        for market, pattern in self.PATTERNS.items():
            if re.match(pattern, symbol):
                return market

        return None

    async def validate_existence(self, symbol: str) -> Dict[str, Any]:
        """Validate if stock exists and get basic info."""
        symbol = symbol.strip().upper()

        # Check cache first
        cache_key = cache.get_stock_cache_key(symbol, "validation")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            # Use yfinance to validate
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info or "symbol" not in info:
                return {
                    "valid": False,
                    "symbol": symbol,
                    "error": "Stock not found",
                }

            result = {
                "valid": True,
                "symbol": symbol,
                "name": info.get("longName", info.get("shortName", symbol)),
                "market": self.get_market(symbol),
                "exchange": info.get("exchange"),
                "currency": info.get("currency"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "validated_at": datetime.utcnow().isoformat(),
            }

            # Cache result for 1 hour
            cache.set(cache_key, result, expire=3600)

            return result

        except Exception as e:
            return {
                "valid": False,
                "symbol": symbol,
                "error": str(e),
            }

    async def batch_validate(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Validate multiple stock codes."""
        results = []
        for symbol in symbols:
            result = await self.validate_existence(symbol)
            results.append(result)
        return results

    def suggest_similar(self, symbol: str, limit: int = 5) -> List[str]:
        """Suggest similar stock codes."""
        symbol = symbol.strip().upper()

        # Common suggestions based on partial match
        suggestions = []

        # US stocks
        if len(symbol) <= 5 and symbol.isalpha():
            common_us = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "JNJ"]
            suggestions.extend([s for s in common_us if s.startswith(symbol[:2])])

        # Chinese stocks
        if symbol.isdigit():
            common_cn = ["600519.SH", "000858.SZ", "601318.SH", "000333.SZ", "002415.SZ"]
            suggestions.extend([s for s in common_cn if s.startswith(symbol[:3])])

        return suggestions[:limit]


# Global validator instance
stock_validator = StockValidator()
