from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
import httpx

from app.core.config import settings
from app.core.cache import cache

logger = logging.getLogger(__name__)


class SentimentResult:
    """Sentiment analysis result."""

    def __init__(self, score: float, label: str, confidence: float):
        self.score = score  # -1.0 to 1.0
        self.label = label  # positive, negative, neutral
        self.confidence = confidence  # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "label": self.label,
            "confidence": self.confidence,
        }


class NewsService:
    """Service for news search and sentiment analysis."""

    def __init__(self):
        self.source = "news_aggregator"

    async def search_news(
        self,
        symbol: str,
        days: int = 7,
        limit: int = 20,
        sources: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Search news for a stock symbol."""
        cache_key = cache.get_stock_cache_key(symbol, f"news_{days}_{limit}")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            # Aggregate news from multiple sources
            all_news = []

            # Yahoo Finance news
            yahoo_news = await self._fetch_yahoo_news(symbol, days, limit)
            all_news.extend(yahoo_news)

            # Sort by date
            all_news.sort(
                key=lambda x: x.get("published_at", ""),
                reverse=True,
            )

            # Limit results
            all_news = all_news[:limit]

            # Add sentiment analysis
            for article in all_news:
                article["sentiment"] = await self._analyze_sentiment(
                    article.get("title", ""),
                    article.get("description", ""),
                )

            result = {
                "symbol": symbol,
                "news": all_news,
                "total": len(all_news),
                "sources": list(set(n.get("source") for n in all_news)),
                "date_range": {
                    "start": (datetime.utcnow() - timedelta(days=days)).isoformat(),
                    "end": datetime.utcnow().isoformat(),
                },
                "fetched_at": datetime.utcnow().isoformat(),
            }

            # Cache for 30 minutes
            cache.set(cache_key, result, expire=1800)

            return result

        except Exception as e:
            logger.error(f"Error searching news for {symbol}: {e}")
            raise

    async def get_sentiment_summary(
        self,
        symbol: str,
        days: int = 7,
    ) -> Dict[str, Any]:
        """Get sentiment summary for a stock."""
        news_result = await self.search_news(symbol, days)

        sentiments = [
            article.get("sentiment", {})
            for article in news_result.get("news", [])
        ]

        if not sentiments:
            return {
                "symbol": symbol,
                "overall_sentiment": "neutral",
                "average_score": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "total_articles": 0,
            }

        scores = [s.get("score", 0) for s in sentiments]
        average_score = sum(scores) / len(scores)

        positive_count = sum(1 for s in sentiments if s.get("label") == "positive")
        negative_count = sum(1 for s in sentiments if s.get("label") == "negative")
        neutral_count = sum(1 for s in sentiments if s.get("label") == "neutral")

        if average_score > 0.2:
            overall_sentiment = "positive"
        elif average_score < -0.2:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"

        return {
            "symbol": symbol,
            "overall_sentiment": overall_sentiment,
            "average_score": round(average_score, 3),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "total_articles": len(sentiments),
            "date_range": news_result.get("date_range"),
        }

    async def _fetch_yahoo_news(
        self,
        symbol: str,
        days: int,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Fetch news from Yahoo Finance."""
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            news = ticker.news

            if not news:
                return []

            parsed_news = []
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            for article in news[:limit]:
                published_at = datetime.utcfromtimestamp(
                    article.get("providerPublishTime", 0)
                )

                if published_at < cutoff_date:
                    continue

                parsed_news.append({
                    "title": article.get("title"),
                    "description": article.get("summary"),
                    "url": article.get("link"),
                    "source": article.get("publisher"),
                    "published_at": published_at.isoformat(),
                    "thumbnail": article.get("thumbnail", {}).get("resolutions", [{}])[0].get("url"),
                })

            return parsed_news

        except Exception as e:
            logger.error(f"Error fetching Yahoo news for {symbol}: {e}")
            return []

    async def _analyze_sentiment(
        self,
        title: str,
        description: str,
    ) -> Dict[str, Any]:
        """Analyze sentiment of text."""
        # Simple keyword-based sentiment analysis
        # In production, use a proper NLP model or API

        positive_keywords = [
            "up", "rise", "gain", "profit", "growth", "bullish",
            "positive", "strong", "buy", "upgrade", "outperform",
            "beat", "exceed", "record", "high", "surge",
        ]

        negative_keywords = [
            "down", "fall", "loss", "decline", "bearish", "negative",
            "weak", "sell", "downgrade", "underperform", "miss",
            "low", "drop", "crash", "recession", "crisis",
        ]

        text = f"{title} {description}".lower()

        positive_count = sum(1 for word in positive_keywords if word in text)
        negative_count = sum(1 for word in negative_keywords if word in text)

        total = positive_count + negative_count

        if total == 0:
            return SentimentResult(0, "neutral", 0.5).to_dict()

        score = (positive_count - negative_count) / total

        if score > 0.2:
            label = "positive"
        elif score < -0.2:
            label = "negative"
        else:
            label = "neutral"

        confidence = min(abs(score) + 0.3, 1.0)

        return SentimentResult(score, label, confidence).to_dict()


# Global service instance
news_service = NewsService()
