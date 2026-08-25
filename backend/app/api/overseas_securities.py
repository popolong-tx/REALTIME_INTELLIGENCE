"""Versioned overseas-securities market-data endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.data_sources.twelve_data import (
    TwelveDataConfigurationError,
    TwelveDataProviderError,
    twelve_data_service,
)


router = APIRouter(
    prefix="/api/v1/overseas-securities",
    tags=["overseas-securities"],
)


def _provider_error(exc: Exception) -> HTTPException:
    if isinstance(exc, TwelveDataConfigurationError):
        return HTTPException(status_code=503, detail=str(exc))
    if isinstance(exc, TwelveDataProviderError):
        return HTTPException(status_code=502, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail="海外证券 API 请求失败。")


@router.get("/providers")
async def list_overseas_providers():
    """Expose provider capabilities and configuration state without secrets."""
    return {
        "schema_version": "2026-08-25",
        "default_provider": "twelve_data",
        "providers": [twelve_data_service.status()],
        "disclaimer": "数据时效、交易所覆盖和再分发权利取决于供应商套餐与市场授权。",
    }


@router.get("/search")
async def search_overseas_securities(
    q: str = Query(..., min_length=1, max_length=120),
    country: Optional[str] = Query(None, max_length=80),
    exchange: Optional[str] = Query(None, max_length=40),
    limit: int = Query(10, ge=1, le=50),
):
    """Search the configured global equity catalogue."""
    try:
        return await twelve_data_service.search_symbols(
            q, country=country, exchange=exchange, limit=limit
        )
    except Exception as exc:
        raise _provider_error(exc) from exc


@router.get("/health/provider")
async def overseas_provider_health(
    probe: bool = Query(False),
    symbol: str = Query("AAPL", max_length=40),
):
    """Report configuration and optionally spend one quote request to probe it."""
    status = twelve_data_service.status()
    if not probe or not status["configured"]:
        return status
    try:
        quote = await twelve_data_service.get_stock_info(symbol)
        return {
            **status,
            "status": "operational",
            "probe_symbol": quote.get("symbol"),
            "probe_source": quote.get("source"),
            "checked_at": quote.get("fetched_at"),
        }
    except Exception as exc:
        raise _provider_error(exc) from exc


@router.get("/{symbol}/quote")
async def get_overseas_quote(
    symbol: str,
    country: Optional[str] = Query(None, max_length=80),
    exchange: Optional[str] = Query(None, max_length=40),
):
    """Return a normalized overseas-equity quote with provider provenance."""
    try:
        return await twelve_data_service.get_stock_info(
            symbol, country=country, exchange=exchange
        )
    except Exception as exc:
        raise _provider_error(exc) from exc


@router.get("/{symbol}/historical")
async def get_overseas_history(
    symbol: str,
    period: str = Query("1y", pattern="^(5d|1mo|3mo|6mo|1y|2y|5y|10y|max)$"),
    interval: str = Query(
        "1d",
        pattern="^(1m|5m|15m|30m|45m|60m|1h|2h|4h|8h|1d|1day|1wk|1week|1mo|1month)$",
    ),
    country: Optional[str] = Query(None, max_length=80),
    exchange: Optional[str] = Query(None, max_length=40),
    outputsize: Optional[int] = Query(None, ge=1, le=5000),
):
    """Return normalized overseas-equity OHLCV history."""
    try:
        return await twelve_data_service.get_historical_data(
            symbol,
            period=period,
            interval=interval,
            country=country,
            exchange=exchange,
            outputsize=outputsize,
        )
    except Exception as exc:
        raise _provider_error(exc) from exc
