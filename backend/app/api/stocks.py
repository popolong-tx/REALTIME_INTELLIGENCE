from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.cache import cache
from app.services.stock_validator import stock_validator
from app.services.stock_info_service import stock_info_service
from app.services.historical_data_service import historical_data_service
from app.services.technical_indicators_service import technical_indicators_service
from app.services.news_service import news_service
from app.services.financial_data_service import financial_data_service

router = APIRouter(prefix="/api/v1/stocks", tags=["stocks"])


# Response Models
class StockInfoResponse(BaseModel):
    symbol: str
    name: Optional[str] = None
    market: Optional[str] = None
    exchange: Optional[str] = None
    current_price: Optional[float] = None
    price_change: Optional[float] = None
    price_change_percent: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None


class HistoricalDataResponse(BaseModel):
    symbol: str
    period: str
    interval: str
    data: List[dict]
    data_quality: dict


class TechnicalAnalysisResponse(BaseModel):
    symbol: str
    indicators: dict
    signals: dict


class NewsResponse(BaseModel):
    symbol: str
    news: List[dict]
    total: int


class SentimentResponse(BaseModel):
    symbol: str
    overall_sentiment: str
    average_score: float
    positive_count: int
    negative_count: int


class FinancialDataResponse(BaseModel):
    symbol: str
    key_metrics: dict


# Endpoints
@router.get("/{symbol}/info", response_model=StockInfoResponse)
async def get_stock_info(symbol: str):
    """Get comprehensive stock information."""
    try:
        info = await stock_info_service.get_stock_overview(symbol)
        return StockInfoResponse(**info)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{symbol}/historical", response_model=HistoricalDataResponse)
async def get_historical_data(
    symbol: str,
    period: str = Query("1y", description="Data period"),
    interval: str = Query("1d", description="Data interval"),
):
    """Get historical price data."""
    try:
        data = await historical_data_service.get_historical_prices(
            symbol, period=period, interval=interval
        )
        return HistoricalDataResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{symbol}/technical", response_model=TechnicalAnalysisResponse)
async def get_technical_analysis(
    symbol: str,
    period: str = Query("1y", description="Analysis period"),
):
    """Get technical analysis indicators."""
    try:
        analysis = await technical_indicators_service.get_technical_analysis(
            symbol, period=period
        )
        return TechnicalAnalysisResponse(**analysis)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{symbol}/news", response_model=NewsResponse)
async def get_stock_news(
    symbol: str,
    days: int = Query(7, description="Number of days"),
    limit: int = Query(20, description="Max results"),
):
    """Get news for a stock."""
    try:
        news = await news_service.search_news(symbol, days=days, limit=limit)
        return NewsResponse(**news)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{symbol}/sentiment", response_model=SentimentResponse)
async def get_stock_sentiment(
    symbol: str,
    days: int = Query(7, description="Number of days"),
):
    """Get sentiment analysis for a stock."""
    try:
        sentiment = await news_service.get_sentiment_summary(symbol, days=days)
        return SentimentResponse(**sentiment)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{symbol}/financials", response_model=FinancialDataResponse)
async def get_financial_data(symbol: str):
    """Get financial data and key metrics."""
    try:
        metrics = await financial_data_service.get_key_metrics(symbol)
        return FinancialDataResponse(
            symbol=str(metrics.get("symbol") or symbol).upper(),
            key_metrics=metrics,
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/search")
async def search_stocks(
    q: str = Query(..., min_length=1, description="Search query"),
    market: Optional[str] = Query(None, description="Filter by market"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
):
    """Search stocks by name or symbol."""
    try:
        results = await stock_validator.search_stocks(q, market=market, limit=limit)
        return {
            "query": q,
            "results": results,
            "total": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_stocks(symbols: List[str]):
    """Validate multiple stock codes."""
    try:
        results = await stock_validator.batch_validate(symbols)
        valid_count = sum(1 for r in results if r.get("valid"))
        return {
            "results": results,
            "total": len(results),
            "valid_count": valid_count,
            "invalid_count": len(results) - valid_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/autocomplete")
async def autocomplete_stock(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
):
    """Get stock code suggestions for autocomplete."""
    try:
        suggestions = await stock_validator.autocomplete(q, limit)
        return {
            "query": q,
            "suggestions": suggestions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
