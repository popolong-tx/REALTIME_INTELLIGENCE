from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.services.recommendation_engine import (
    recommendation_engine,
    TradingRecommendation,
    RecommendationType,
    RiskLevel,
    TimeHorizon,
)
from app.services.stock_info_service import stock_info_service
from app.services.technical_indicators_service import technical_indicators_service
from app.services.news_service import news_service
from app.services.financial_data_service import financial_data_service
from app.core.cache import cache

logger = logging.getLogger(__name__)


class SingleStockRecommendationService:
    """Service for generating single stock recommendations."""

    async def get_recommendation(
        self,
        symbol: str,
        user_profile: Optional[Dict[str, Any]] = None,
        include_analysis: bool = True,
    ) -> Dict[str, Any]:
        """Get comprehensive recommendation for a single stock."""
        # Check cache
        cache_key = cache.get_stock_cache_key(symbol, "recommendation")
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            # Generate recommendation
            recommendation = await recommendation_engine.generate_recommendation(
                symbol, user_profile
            )

            result = recommendation.to_dict()

            # Add detailed analysis if requested
            if include_analysis:
                result["detailed_analysis"] = await self._get_detailed_analysis(symbol)

            # Add summary
            result["summary"] = self._generate_summary(recommendation)

            # Cache for 15 minutes
            cache.set(cache_key, result, expire=900)

            return result

        except Exception as e:
            logger.error(f"Error getting recommendation for {symbol}: {e}")
            raise

    async def get_quick_recommendation(
        self,
        symbol: str,
    ) -> Dict[str, Any]:
        """Get quick recommendation without detailed analysis."""
        try:
            recommendation = await recommendation_engine.generate_recommendation(symbol)

            return {
                "symbol": symbol,
                "recommendation": recommendation.recommendation.value,
                "confidence": recommendation.confidence,
                "risk_level": recommendation.risk_level.value,
                "target_price": recommendation.target_price,
                "stop_loss": recommendation.stop_loss,
                "summary": self._generate_summary(recommendation),
            }

        except Exception as e:
            logger.error(f"Error getting quick recommendation for {symbol}: {e}")
            raise

    async def compare_recommendations(
        self,
        symbols: List[str],
    ) -> Dict[str, Any]:
        """Compare recommendations for multiple stocks."""
        recommendations = []

        for symbol in symbols:
            try:
                rec = await self.get_quick_recommendation(symbol)
                recommendations.append(rec)
            except Exception as e:
                logger.error(f"Error getting recommendation for {symbol}: {e}")
                recommendations.append({
                    "symbol": symbol,
                    "error": str(e),
                })

        # Sort by confidence
        valid_recs = [r for r in recommendations if "error" not in r]
        valid_recs.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        return {
            "recommendations": recommendations,
            "best_recommendation": valid_recs[0] if valid_recs else None,
            "total": len(recommendations),
            "successful": len(valid_recs),
        }

    async def _get_detailed_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get detailed analysis for a stock."""
        try:
            # Get all data in parallel
            stock_info = await stock_info_service.get_stock_overview(symbol)
            technical = await technical_indicators_service.get_technical_analysis(symbol)
            news = await news_service.search_news(symbol, days=7)
            sentiment = await news_service.get_sentiment_summary(symbol, days=7)
            financials = await financial_data_service.get_key_metrics(symbol)

            return {
                "stock_info": stock_info,
                "technical_analysis": technical,
                "news_summary": {
                    "count": news.get("total", 0),
                    "recent": news.get("news", [])[:3],
                },
                "sentiment": sentiment,
                "financial_metrics": financials,
            }

        except Exception as e:
            logger.error(f"Error getting detailed analysis for {symbol}: {e}")
            return {"error": str(e)}

    def _generate_summary(self, recommendation: TradingRecommendation) -> str:
        """Generate a concise summary of the recommendation."""
        rec = recommendation.recommendation
        confidence = recommendation.confidence
        risk = recommendation.risk_level

        summary_parts = []

        # Main recommendation
        if rec == RecommendationType.BUY:
            summary_parts.append(f"建议买入 {recommendation.symbol}")
        elif rec == RecommendationType.SELL:
            summary_parts.append(f"建议卖出 {recommendation.symbol}")
        elif rec == RecommendationType.HOLD:
            summary_parts.append(f"建议持有 {recommendation.symbol}")
        else:
            summary_parts.append(f"建议回避 {recommendation.symbol}")

        # Confidence
        if confidence >= 0.8:
            summary_parts.append("信心度高")
        elif confidence >= 0.6:
            summary_parts.append("信心度中等")
        else:
            summary_parts.append("信心度低")

        # Risk
        if risk in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            summary_parts.append("风险较高")

        # Price targets
        if recommendation.target_price:
            summary_parts.append(f"目标价 {recommendation.target_price}")

        if recommendation.stop_loss:
            summary_parts.append(f"止损价 {recommendation.stop_loss}")

        return "，".join(summary_parts)


# Global service instance
single_stock_recommendation_service = SingleStockRecommendationService()
