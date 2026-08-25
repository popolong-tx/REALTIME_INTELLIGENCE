"""Twelve Data adapter for governed overseas-securities market data."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx

from app.core.cache import cache
from app.core.config import settings


class TwelveDataConfigurationError(RuntimeError):
    """Raised when the server-side provider configuration is incomplete."""


class TwelveDataProviderError(RuntimeError):
    """Raised for sanitized provider and entitlement failures."""


class TwelveDataService:
    """Normalize Twelve Data search, quote, and OHLCV responses."""

    source = "twelve_data"
    _interval_map = {
        "1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min",
        "45m": "45min", "60m": "1h", "1h": "1h", "2h": "2h",
        "4h": "4h", "8h": "8h", "1d": "1day", "1day": "1day",
        "1wk": "1week", "1week": "1week", "1mo": "1month",
        "1month": "1month",
    }
    _period_points = {
        "5d": 500, "1mo": 32, "3mo": 96, "6mo": 190, "1y": 370,
        "2y": 740, "5y": 1830, "10y": 3660, "max": 5000,
    }

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        self.api_key = api_key if api_key is not None else settings.TWELVE_DATA_API_KEY
        self.base_url = (
            base_url if base_url is not None else settings.TWELVE_DATA_BASE_URL
        ).rstrip("/")

    @property
    def configured(self) -> bool:
        parsed = urlparse(self.base_url)
        return bool(self.api_key and parsed.scheme == "https" and parsed.hostname)

    def status(self) -> Dict[str, Any]:
        return {
            "provider": self.source,
            "status": "configured" if self.configured else "configuration_required",
            "configured": self.configured,
            "base_url": self.base_url,
            "capabilities": ["symbol_search", "quote", "time_series"],
            "market_scope": "global_equities",
            "freshness": "按交易所与供应商套餐授权返回实时、延迟或日终数据",
            "required_secret": "TWELVE_DATA_API_KEY",
        }

    def _require_configuration(self) -> None:
        if not self.configured:
            raise TwelveDataConfigurationError(
                "海外证券 API 尚未配置，请在服务端环境变量中设置 TWELVE_DATA_API_KEY。"
            )

    async def _request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        self._require_configuration()
        request_params = {
            key: value for key, value in params.items() if value not in (None, "")
        }
        request_params["apikey"] = self.api_key
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0),
                follow_redirects=False,
            ) as client:
                response = await client.get(endpoint, params=request_params)
        except httpx.TimeoutException as exc:
            raise TwelveDataProviderError("海外证券 API 响应超时。") from exc
        except httpx.HTTPError as exc:
            raise TwelveDataProviderError("海外证券 API 网络连接失败。") from exc

        if response.status_code >= 400:
            raise TwelveDataProviderError(
                f"海外证券 API 返回 HTTP {response.status_code}。"
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise TwelveDataProviderError("海外证券 API 返回了无法解析的数据。") from exc
        if not isinstance(payload, dict):
            raise TwelveDataProviderError("海外证券 API 返回格式不正确。")
        if payload.get("status") == "error" or payload.get("code"):
            message = str(payload.get("message") or "供应商拒绝了本次请求。")
            raise TwelveDataProviderError(f"海外证券 API：{message[:240]}")
        return payload

    @staticmethod
    def _number(value: Any) -> Optional[float]:
        if value in (None, "", "null", "None"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _integer(value: Any) -> Optional[int]:
        number = TwelveDataService._number(value)
        return int(number) if number is not None else None

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        normalized = str(symbol or "").strip().upper()
        if not normalized or len(normalized) > 40:
            raise ValueError("证券代码长度不正确。")
        if not re.fullmatch(r"[A-Z0-9.:-]+", normalized):
            raise ValueError("证券代码只能包含字母、数字、点、冒号或连字符。")
        return normalized

    async def search_symbols(
        self,
        query: str,
        *,
        country: Optional[str] = None,
        exchange: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        normalized_query = str(query or "").strip()
        if not normalized_query:
            raise ValueError("请输入证券代码或公司名称。")
        payload = await self._request(
            "/symbol_search",
            {
                "symbol": normalized_query,
                "country": country,
                "exchange": exchange,
                "outputsize": max(1, min(int(limit), 50)),
            },
        )
        results = []
        for item in (payload.get("data") or [])[: max(1, min(int(limit), 50))]:
            if not isinstance(item, dict):
                continue
            results.append({
                "symbol": item.get("symbol"),
                "name": item.get("instrument_name") or item.get("name"),
                "exchange": item.get("exchange"),
                "mic_code": item.get("mic_code"),
                "country": item.get("country"),
                "currency": item.get("currency"),
                "instrument_type": item.get("instrument_type"),
                "access": item.get("access"),
                "source": self.source,
            })
        return {
            "query": normalized_query,
            "results": results,
            "total": len(results),
            "source": self.source,
            "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

    async def get_stock_info(
        self,
        symbol: str,
        *,
        exchange: Optional[str] = None,
        country: Optional[str] = None,
    ) -> Dict[str, Any]:
        normalized_symbol = self.normalize_symbol(symbol)
        cache_key = cache.get_stock_cache_key(
            normalized_symbol, f"twelve_quote_{exchange or '-'}_{country or '-'}"
        )
        cached = cache.get(cache_key)
        if cached:
            return cached
        data = await self._request(
            "/quote",
            {"symbol": normalized_symbol, "exchange": exchange, "country": country},
        )
        current_price = self._number(data.get("close") or data.get("price"))
        previous_close = self._number(data.get("previous_close"))
        result = {
            "symbol": data.get("symbol") or normalized_symbol,
            "name": data.get("name"),
            "market": data.get("country"),
            "exchange": data.get("exchange"),
            "mic_code": data.get("mic_code"),
            "currency": data.get("currency"),
            "current_price": current_price,
            "previous_close": previous_close,
            "open": self._number(data.get("open")),
            "day_high": self._number(data.get("high")),
            "day_low": self._number(data.get("low")),
            "volume": self._integer(data.get("volume")),
            "avg_volume": self._integer(data.get("average_volume")),
            "price_change": self._number(data.get("change")),
            "price_change_percent": self._number(data.get("percent_change")),
            "fifty_two_week_high": self._number((data.get("fifty_two_week") or {}).get("high")),
            "fifty_two_week_low": self._number((data.get("fifty_two_week") or {}).get("low")),
            "is_market_open": data.get("is_market_open"),
            "provider_timestamp": data.get("datetime") or data.get("timestamp"),
            "source": self.source,
            "market_scope": "overseas",
            "freshness_note": "时效取决于交易所授权和 Twelve Data 套餐。",
            "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        if result["price_change"] is None and current_price is not None and previous_close:
            result["price_change"] = round(current_price - previous_close, 6)
        if result["price_change_percent"] is None and current_price is not None and previous_close:
            result["price_change_percent"] = round(
                (current_price - previous_close) / previous_close * 100, 6
            )
        cache.set(cache_key, result, expire=300)
        return result

    async def get_historical_data(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        *,
        exchange: Optional[str] = None,
        country: Optional[str] = None,
        outputsize: Optional[int] = None,
    ) -> Dict[str, Any]:
        normalized_symbol = self.normalize_symbol(symbol)
        normalized_interval = self._interval_map.get(str(interval).lower())
        if not normalized_interval:
            raise ValueError("不支持的行情周期。")
        points = max(1, min(int(outputsize or self._period_points.get(str(period).lower(), 370)), 5000))
        cache_key = cache.get_stock_cache_key(
            normalized_symbol,
            f"twelve_history_{period}_{normalized_interval}_{exchange or '-'}_{country or '-'}_{points}",
        )
        cached = cache.get(cache_key)
        if cached:
            return cached
        payload = await self._request(
            "/time_series",
            {
                "symbol": normalized_symbol,
                "interval": normalized_interval,
                "exchange": exchange,
                "country": country,
                "outputsize": points,
                "order": "ASC",
                "timezone": "Exchange",
            },
        )
        meta = payload.get("meta") or {}
        rows = []
        for item in payload.get("values") or []:
            if not isinstance(item, dict):
                continue
            date_value = item.get("datetime")
            rows.append({
                "date": str(date_value or "").split(" ", 1)[0],
                "datetime": date_value,
                "open": self._number(item.get("open")),
                "high": self._number(item.get("high")),
                "low": self._number(item.get("low")),
                "close": self._number(item.get("close")),
                "volume": self._integer(item.get("volume")),
            })
        if not rows:
            raise TwelveDataProviderError("海外证券 API 未返回历史行情。")
        result = {
            "symbol": meta.get("symbol") or normalized_symbol,
            "period": period,
            "interval": interval,
            "provider_interval": normalized_interval,
            "exchange": meta.get("exchange"),
            "mic_code": meta.get("mic_code"),
            "currency": meta.get("currency"),
            "exchange_timezone": meta.get("exchange_timezone"),
            "data": rows,
            "source": self.source,
            "market_scope": "overseas",
            "freshness_note": "日线按交易所本地时间返回；实时性取决于供应商套餐。",
            "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        cache.set(cache_key, result, expire=900 if normalized_interval != "1day" else 3600)
        return result

    async def get_intraday_data(
        self, symbol: str, interval: str = "5min", outputsize: int = 500
    ) -> Dict[str, Any]:
        return await self.get_historical_data(
            symbol, period="5d", interval=interval, outputsize=outputsize
        )


twelve_data_service = TwelveDataService()
