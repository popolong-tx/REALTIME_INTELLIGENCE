from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from urllib.parse import urlparse
import logging

from app.core.cache import cache
from app.services.oci_responses_service import oci_responses_service

logger = logging.getLogger(__name__)


class XSearchService:
    """X research adapter backed by OCI Grok's built-in X Search tool."""

    def __init__(self):
        self.provider = "oci-grok-x-search"

    async def search_tweets(
        self,
        query: str,
        max_results: int = 10,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        tweet_fields: Optional[List[str]] = None,
        user_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Search public X content through the OCI Responses API.

        X opinions and claimed trades remain unverified. Citation URLs are
        normalized into the legacy ``tweets`` shape for existing API callers.
        """
        cache_key = f"x_search:{query}:{max_results}:{start_time}:{end_time}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        result = await oci_responses_service.search_x(
            query=query,
            max_results=min(max_results, 100),
            from_date=start_time.strftime("%Y-%m-%d") if start_time else None,
            to_date=end_time.strftime("%Y-%m-%d") if end_time else None,
        )
        citations = result.get("citations") or []
        tweets = []
        for index, citation in enumerate(citations[:max_results]):
            url = citation.get("url", "")
            parts = [part for part in urlparse(url).path.split("/") if part]
            username = parts[0] if len(parts) >= 1 else None
            post_id = parts[2] if len(parts) >= 3 and parts[1] == "status" else str(index)
            tweets.append({
                "id": post_id,
                "text": citation.get("text") or citation.get("title") or "",
                "created_at": None,
                "author": {
                    "id": None,
                    "name": username,
                    "username": username,
                    "verified": False,
                    "followers_count": None,
                },
                "metrics": {},
                "entities": {},
                "context_annotations": [],
                "url": url,
                "verification_status": "unverified_opinion",
            })

        parsed_result = {
            "tweets": tweets,
            "count": len(tweets),
            "summary": result.get("inferenceResponse", {}).get("text", ""),
            "citations": citations,
            "metadata": {
                "provider": self.provider,
                "model_id": result.get("metadata", {}).get("model_id"),
                "query": query,
                "max_results": max_results,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "searched_at": datetime.utcnow().isoformat(),
            },
        }
        cache.set(cache_key, parsed_result, expire=900)
        return parsed_result

    async def search_stock_mentions(
        self,
        symbol: str,
        days: int = 7,
        max_results: int = 20,
    ) -> Dict[str, Any]:
        """Search for stock mentions on X."""
        # Build query for stock mentions
        query = f"${symbol} OR #{symbol} stock"

        start_time = datetime.utcnow() - timedelta(days=days)

        return await self.search_tweets(
            query=query,
            max_results=max_results,
            start_time=start_time,
        )

    async def search_financial_news(
        self,
        topic: str,
        days: int = 1,
        max_results: int = 10,
    ) -> Dict[str, Any]:
        """Search for financial news on X."""
        query = f"{topic} (stock OR market OR trading OR investment)"

        start_time = datetime.utcnow() - timedelta(days=days)

        return await self.search_tweets(
            query=query,
            max_results=max_results,
            start_time=start_time,
        )

    async def search_user_tweets(
        self,
        username: str,
        max_results: int = 10,
    ) -> Dict[str, Any]:
        """Search tweets from a specific user."""
        query = f"from:{username}"

        return await self.search_tweets(
            query=query,
            max_results=max_results,
        )

    def _parse_search_results(
        self,
        raw_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse X Search API results."""
        tweets = raw_result.get("data", [])
        users = raw_result.get("includes", {}).get("users", [])
        meta = raw_result.get("meta", {})

        # Create user lookup
        user_lookup = {user["id"]: user for user in users}

        # Parse tweets
        parsed_tweets = []
        for tweet in tweets:
            author_id = tweet.get("author_id")
            author = user_lookup.get(author_id, {})

            parsed_tweet = {
                "id": tweet.get("id"),
                "text": tweet.get("text"),
                "created_at": tweet.get("created_at"),
                "author": {
                    "id": author_id,
                    "name": author.get("name"),
                    "username": author.get("username"),
                    "verified": author.get("verified", False),
                    "followers_count": author.get("public_metrics", {}).get("followers_count"),
                },
                "metrics": tweet.get("public_metrics", {}),
                "entities": tweet.get("entities", {}),
                "context_annotations": tweet.get("context_annotations", []),
                "url": f"https://x.com/{author.get('username')}/status/{tweet.get('id')}",
            }

            parsed_tweets.append(parsed_tweet)

        return {
            "tweets": parsed_tweets,
            "count": len(parsed_tweets),
            "meta": meta,
        }

    def extract_sentiment_from_tweets(
        self,
        tweets: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Extract sentiment from tweets."""
        if not tweets:
            return {
                "overall_sentiment": "neutral",
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "total_count": 0,
            }

        positive_keywords = [
            "bullish", "buy", "moon", "rocket", "up", "gain", "profit",
            "positive", "strong", "growth", "outperform", "beat",
        ]

        negative_keywords = [
            "bearish", "sell", "down", "crash", "loss", "decline",
            "negative", "weak", "underperform", "miss", "recession",
        ]

        positive_count = 0
        negative_count = 0
        neutral_count = 0

        for tweet in tweets:
            text = tweet.get("text", "").lower()

            has_positive = any(word in text for word in positive_keywords)
            has_negative = any(word in text for word in negative_keywords)

            if has_positive and not has_negative:
                positive_count += 1
            elif has_negative and not has_positive:
                negative_count += 1
            else:
                neutral_count += 1

        total = positive_count + negative_count + neutral_count

        if positive_count > negative_count:
            overall_sentiment = "positive"
        elif negative_count > positive_count:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"

        return {
            "overall_sentiment": overall_sentiment,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "total_count": total,
            "positive_ratio": positive_count / total if total > 0 else 0,
            "negative_ratio": negative_count / total if total > 0 else 0,
        }


# Global service instance
x_search_service = XSearchService()
