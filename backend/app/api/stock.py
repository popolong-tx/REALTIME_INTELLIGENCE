from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.cache import cache
from app.services.stock_validator import stock_validator

router = APIRouter(prefix="/api/v1/stocks", tags=["stocks"])


class StockValidationResponse(BaseModel):
    valid: bool
    symbol: str
    name: Optional[str] = None
    market: Optional[str] = None
    exchange: Optional[str] = None
    currency: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    error: Optional[str] = None
    validated_at: Optional[str] = None


class BatchValidationRequest(BaseModel):
    symbols: List[str]


class BatchValidationResponse(BaseModel):
    results: List[StockValidationResponse]
    total: int
    valid_count: int
    invalid_count: int


class AutoCompleteResponse(BaseModel):
    symbol: str
    name: Optional[str] = None
    market: Optional[str] = None


@router.get("/validate/{symbol}", response_model=StockValidationResponse)
async def validate_stock(symbol: str):
    """Validate a single stock code."""
    result = await stock_validator.validate_existence(symbol)
    return result


@router.post("/validate/batch", response_model=BatchValidationResponse)
async def validate_stocks_batch(request: BatchValidationRequest):
    """Validate multiple stock codes."""
    results = await stock_validator.batch_validate(request.symbols)

    valid_count = sum(1 for r in results if r.get("valid"))
    invalid_count = len(results) - valid_count

    return BatchValidationResponse(
        results=results,
        total=len(results),
        valid_count=valid_count,
        invalid_count=invalid_count,
    )


@router.get("/autocomplete", response_model=List[AutoCompleteResponse])
async def autocomplete_stock(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
):
    """Get stock code suggestions for autocomplete."""
    # Check cache first
    cache_key = f"autocomplete:{q}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Get suggestions
    suggestions = stock_validator.suggest_similar(q, limit)

    # Enrich with names
    results = []
    for symbol in suggestions:
        validation = await stock_validator.validate_existence(symbol)
        if validation.get("valid"):
            results.append(
                AutoCompleteResponse(
                    symbol=symbol,
                    name=validation.get("name"),
                    market=validation.get("market"),
                )
            )

    # Cache for 5 minutes
    cache.set(cache_key, results, expire=300)

    return results


@router.get("/search")
async def search_stocks(
    q: str = Query(..., min_length=1, description="Search query"),
    market: Optional[str] = Query(None, description="Filter by market"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
):
    """Search stocks by name or symbol."""
    # This would integrate with a stock database or API
    # For now, return basic suggestions
    suggestions = stock_validator.suggest_similar(q, limit)

    results = []
    for symbol in suggestions:
        validation = await stock_validator.validate_existence(symbol)
        if validation.get("valid"):
            if market and validation.get("market") != market:
                continue
            results.append(validation)

    return {
        "query": q,
        "market": market,
        "results": results,
        "total": len(results),
    }
