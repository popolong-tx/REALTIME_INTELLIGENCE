from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.services.data_sources.data_aggregator import data_aggregator
from app.services.news_service import news_service
from app.services.x_search_service import x_search_service
from app.services.oci_responses_service import oci_responses_service

router = APIRouter(prefix="/api/v1/search", tags=["search"])


# Request/Response Models
class SearchRequest(BaseModel):
    query: str
    sources: Optional[List[str]] = None
    limit: int = 20
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class SearchResult(BaseModel):
    source: str
    title: str
    content: str
    url: Optional[str] = None
    published_at: Optional[str] = None
    relevance_score: float


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int
    sources_used: List[str]


# Endpoints
@router.post("/global", response_model=SearchResponse)
async def global_search(request: SearchRequest):
    """Search across all data sources."""
    results = []
    sources_used = []

    # Search news
    if not request.sources or "news" in request.sources:
        try:
            news_results = await news_service.search_news(
                request.query,
                days=7,
                limit=request.limit,
            )
            for news in news_results.get("news", []):
                results.append(SearchResult(
                    source="news",
                    title=news.get("title", ""),
                    content=news.get("description", ""),
                    url=news.get("url"),
                    published_at=news.get("published_at"),
                    relevance_score=0.8,
                ))
            sources_used.append("news")
        except Exception as e:
            pass

    # Search X (Twitter)
    if not request.sources or "x" in request.sources:
        try:
            x_results = await x_search_service.search_tweets(
                request.query,
                max_results=request.limit,
            )
            for tweet in x_results.get("tweets", []):
                results.append(SearchResult(
                    source="x",
                    title=f"@{tweet.get('author', {}).get('username', '')}",
                    content=tweet.get("text", ""),
                    url=tweet.get("url"),
                    published_at=tweet.get("created_at"),
                    relevance_score=0.7,
                ))
            sources_used.append("x")
        except Exception as e:
            pass

    # Sort by relevance
    results.sort(key=lambda x: x.relevance_score, reverse=True)

    return SearchResponse(
        query=request.query,
        results=results[:request.limit],
        total=len(results),
        sources_used=sources_used,
    )


@router.post("/semantic")
async def semantic_search(
    query: str = Query(..., description="Search query"),
    context: Optional[str] = Query(None, description="Additional context"),
):
    """Semantic search using AI."""
    try:
        # Use OCI/Grok for semantic understanding
        result = await oci_responses_service.generate_text(
            prompt=f"Search for: {query}\nContext: {context or 'N/A'}\n\nProvide relevant information and analysis.",
            system_prompt="You are a financial research assistant. Provide comprehensive and accurate information.",
        )

        return {
            "query": query,
            "result": result.get("inferenceResponse", {}).get("text", ""),
            "model": result.get("metadata", {}).get("model_id"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news")
async def search_news(
    q: str = Query(..., description="Search query"),
    days: int = Query(7, description="Number of days"),
    limit: int = Query(20, description="Max results"),
):
    """Search news articles."""
    try:
        results = await news_service.search_news(q, days=days, limit=limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/social")
async def search_social(
    q: str = Query(..., description="Search query"),
    platform: str = Query("x", description="Social platform"),
    days: int = Query(7, description="Number of days"),
    limit: int = Query(20, description="Max results"),
):
    """Search social media."""
    try:
        if platform == "x":
            results = await x_search_service.search_tweets(q, max_results=limit)
            return results
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/financial")
async def search_financial_data(
    symbol: str = Query(..., description="Stock symbol"),
    data_type: str = Query("all", description="Data type"),
):
    """Search financial data."""
    try:
        from app.services.financial_data_service import financial_data_service

        if data_type == "all":
            result = await financial_data_service.get_key_metrics(symbol)
        elif data_type == "ratios":
            result = await financial_data_service.get_financial_ratios(symbol)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported data type: {data_type}")

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market")
async def search_market_data(
    symbols: str = Query(..., description="Comma-separated symbols"),
):
    """Search market data for multiple symbols."""
    try:
        symbol_list = [s.strip() for s in symbols.split(",")]
        results = []

        for symbol in symbol_list[:10]:  # Limit to 10 symbols
            try:
                info = await data_aggregator.get_stock_info(symbol)
                results.append(info)
            except Exception:
                continue

        return {
            "symbols": symbol_list,
            "results": results,
            "total": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
