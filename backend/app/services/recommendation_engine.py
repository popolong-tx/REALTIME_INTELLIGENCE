from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
import logging

from app.services.stock_info_service import stock_info_service
from app.services.technical_indicators_service import technical_indicators_service
from app.services.news_service import news_service
from app.services.xai_grok_service import xai_grok_service
from app.services.verification_service import verification_service

logger = logging.getLogger(__name__)


class RecommendationType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    AVOID = "avoid"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class TimeHorizon(str, Enum):
    SHORT = "short"  # 1-4 weeks
    MEDIUM = "medium"  # 1-3 months
    LONG = "long"  # 3-12 months


class TradingRecommendation:
    """Trading recommendation with detailed analysis."""

    def __init__(
        self,
        symbol: str,
        recommendation: RecommendationType,
        confidence: float,
        risk_level: RiskLevel,
        time_horizon: TimeHorizon,
        entry_price: Optional[float] = None,
        target_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        reasoning: str = "",
        factors: Dict[str, Any] = None,
        citations: List[Dict[str, Any]] = None,
        disclaimers: List[str] = None,
    ):
        self.symbol = symbol
        self.recommendation = recommendation
        self.confidence = confidence
        self.risk_level = risk_level
        self.time_horizon = time_horizon
        self.entry_price = entry_price
        self.target_price = target_price
        self.stop_loss = stop_loss
        self.reasoning = reasoning
        self.factors = factors or {}
        self.citations = citations or []
        self.disclaimers = disclaimers or []
        self.generated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "recommendation": self.recommendation.value,
            "confidence": self.confidence,
            "risk_level": self.risk_level.value,
            "time_horizon": self.time_horizon.value,
            "entry_price": self.entry_price,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
            "reasoning": self.reasoning,
            "factors": self.factors,
            "citations": self.citations,
            "disclaimers": self.disclaimers,
            "generated_at": self.generated_at.isoformat(),
        }


class RecommendationEngine:
    """Core engine for generating trading recommendations."""

    def __init__(self):
        self.min_confidence_threshold = 0.6
        self.max_risk_level = RiskLevel.HIGH

    async def generate_recommendation(
        self,
        symbol: str,
        user_profile: Optional[Dict[str, Any]] = None,
        custom_factors: Optional[Dict[str, Any]] = None,
    ) -> TradingRecommendation:
        """Generate a comprehensive trading recommendation."""
        try:
            # Gather all data
            stock_info = await stock_info_service.get_stock_overview(symbol)
            technical_analysis = await technical_indicators_service.get_technical_analysis(symbol)
            news_data = await news_service.search_news(symbol, days=7)
            sentiment = await news_service.get_sentiment_summary(symbol, days=7)

            # Analyze factors
            factors = await self._analyze_factors(
                stock_info, technical_analysis, news_data, sentiment, custom_factors
            )

            # Calculate overall score
            overall_score = self._calculate_overall_score(factors)

            # Determine recommendation
            recommendation = self._determine_recommendation(overall_score, factors)

            # Calculate confidence
            confidence = self._calculate_confidence(factors)

            # Determine risk level
            risk_level = self._assess_risk_level(stock_info, technical_analysis, factors)

            # Determine time horizon
            time_horizon = self._determine_time_horizon(technical_analysis, factors)

            # Calculate price targets
            price_targets = self._calculate_price_targets(
                stock_info, technical_analysis, recommendation
            )

            # Generate reasoning
            reasoning = await self._generate_reasoning(
                symbol, factors, recommendation, stock_info
            )

            # Get citations
            citations = self._collect_citations(stock_info, news_data)

            # Add disclaimers
            disclaimers = self._generate_disclaimers(recommendation, risk_level)

            return TradingRecommendation(
                symbol=symbol,
                recommendation=recommendation,
                confidence=confidence,
                risk_level=risk_level,
                time_horizon=time_horizon,
                entry_price=price_targets.get("entry"),
                target_price=price_targets.get("target"),
                stop_loss=price_targets.get("stop_loss"),
                reasoning=reasoning,
                factors=factors,
                citations=citations,
                disclaimers=disclaimers,
            )

        except Exception as e:
            logger.error(f"Error generating recommendation for {symbol}: {e}")
            raise

    async def _analyze_factors(
        self,
        stock_info: Dict[str, Any],
        technical_analysis: Dict[str, Any],
        news_data: Dict[str, Any],
        sentiment: Dict[str, Any],
        custom_factors: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze all factors for recommendation."""
        factors = {}

        # Technical factors
        technical_factors = self._analyze_technical_factors(technical_analysis)
        factors["technical"] = technical_factors

        # Fundamental factors
        fundamental_factors = self._analyze_fundamental_factors(stock_info)
        factors["fundamental"] = fundamental_factors

        # Sentiment factors
        sentiment_factors = self._analyze_sentiment_factors(sentiment)
        factors["sentiment"] = sentiment_factors

        # News factors
        news_factors = self._analyze_news_factors(news_data)
        factors["news"] = news_factors

        # Custom factors
        if custom_factors:
            factors["custom"] = custom_factors

        return factors

    def _analyze_technical_factors(self, technical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical indicators."""
        indicators = technical_analysis.get("indicators", {})
        signals = technical_analysis.get("signals", {})

        # Moving averages
        ma_signals = indicators.get("moving_averages", {})
        ma_positions = ma_signals.get("positions", {})
        bullish_mas = sum(1 for pos in ma_positions.values() if pos == "above")
        bearish_mas = sum(1 for pos in ma_positions.values() if pos == "below")

        # Oscillators
        oscillators = indicators.get("oscillators", {})
        rsi = oscillators.get("rsi", {})
        macd = oscillators.get("macd", {})

        # Overall technical score
        technical_score = 0.5  # Neutral

        if bullish_mas > bearish_mas:
            technical_score += 0.1
        elif bearish_mas > bullish_mas:
            technical_score -= 0.1

        if rsi.get("signal") == "oversold":
            technical_score += 0.15
        elif rsi.get("signal") == "overbought":
            technical_score -= 0.15

        if macd.get("signal") == "bullish_crossover":
            technical_score += 0.2
        elif macd.get("signal") == "bearish_crossover":
            technical_score -= 0.2

        return {
            "score": min(max(technical_score, 0), 1),
            "moving_averages": {
                "bullish_count": bullish_mas,
                "bearish_count": bearish_mas,
                "positions": ma_positions,
            },
            "rsi": rsi,
            "macd": macd,
            "overall_signal": signals.get("overall_signal", "neutral"),
        }

    def _analyze_fundamental_factors(self, stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze fundamental factors."""
        pe_ratio = stock_info.get("pe_ratio")
        market_cap = stock_info.get("market_cap")
        dividend_yield = stock_info.get("dividend_yield")

        fundamental_score = 0.5  # Neutral

        # P/E ratio analysis
        if pe_ratio:
            if pe_ratio < 15:
                fundamental_score += 0.15  # Undervalued
            elif pe_ratio > 30:
                fundamental_score -= 0.15  # Overvalued

        # Market cap stability
        if market_cap:
            if market_cap > 10_000_000_000:  # Large cap
                fundamental_score += 0.1
            elif market_cap < 1_000_000_000:  # Small cap
                fundamental_score -= 0.05

        # Dividend yield
        if dividend_yield and dividend_yield > 0.03:
            fundamental_score += 0.1

        return {
            "score": min(max(fundamental_score, 0), 1),
            "pe_ratio": pe_ratio,
            "market_cap": market_cap,
            "dividend_yield": dividend_yield,
            "sector": stock_info.get("sector"),
            "industry": stock_info.get("industry"),
        }

    def _analyze_sentiment_factors(self, sentiment: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment factors."""
        overall_sentiment = sentiment.get("overall_sentiment", "neutral")
        average_score = sentiment.get("average_score", 0)

        sentiment_score = 0.5  # Neutral

        if overall_sentiment == "positive":
            sentiment_score += 0.2
        elif overall_sentiment == "negative":
            sentiment_score -= 0.2

        # Adjust by average score
        sentiment_score += average_score * 0.3

        return {
            "score": min(max(sentiment_score, 0), 1),
            "overall_sentiment": overall_sentiment,
            "average_score": average_score,
            "positive_count": sentiment.get("positive_count", 0),
            "negative_count": sentiment.get("negative_count", 0),
            "total_articles": sentiment.get("total_articles", 0),
        }

    def _analyze_news_factors(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze news factors."""
        news = news_data.get("news", [])

        if not news:
            return {
                "score": 0.5,
                "news_count": 0,
                "recent_news": [],
            }

        # Calculate average sentiment from news
        sentiments = [n.get("sentiment", {}).get("score", 0) for n in news]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

        news_score = 0.5 + avg_sentiment * 0.3

        return {
            "score": min(max(news_score, 0), 1),
            "news_count": len(news),
            "average_sentiment": avg_sentiment,
            "recent_news": news[:5],  # Top 5 recent news
        }

    def _calculate_overall_score(self, factors: Dict[str, Any]) -> float:
        """Calculate overall recommendation score."""
        weights = {
            "technical": 0.35,
            "fundamental": 0.25,
            "sentiment": 0.20,
            "news": 0.20,
        }

        score = 0.0
        total_weight = 0.0

        for factor_name, weight in weights.items():
            if factor_name in factors:
                factor_score = factors[factor_name].get("score", 0.5)
                score += factor_score * weight
                total_weight += weight

        if total_weight > 0:
            score /= total_weight

        return score

    def _determine_recommendation(
        self,
        overall_score: float,
        factors: Dict[str, Any],
    ) -> RecommendationType:
        """Determine recommendation based on score."""
        if overall_score >= 0.7:
            return RecommendationType.BUY
        elif overall_score >= 0.6:
            return RecommendationType.HOLD
        elif overall_score >= 0.4:
            return RecommendationType.HOLD
        elif overall_score >= 0.3:
            return RecommendationType.SELL
        else:
            return RecommendationType.AVOID

    def _calculate_confidence(self, factors: Dict[str, Any]) -> float:
        """Calculate confidence in recommendation."""
        # Calculate based on factor consistency
        scores = []
        for factor in factors.values():
            if isinstance(factor, dict) and "score" in factor:
                scores.append(factor["score"])

        if not scores:
            return 0.5

        # Higher confidence when factors agree
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        consistency = 1 - min(variance * 4, 1)  # Normalize

        return round(consistency, 2)

    def _assess_risk_level(
        self,
        stock_info: Dict[str, Any],
        technical_analysis: Dict[str, Any],
        factors: Dict[str, Any],
    ) -> RiskLevel:
        """Assess risk level."""
        risk_score = 0

        # Volatility
        atr = technical_analysis.get("indicators", {}).get("volatility", {}).get("atr", {})
        if atr.get("percent", 0) > 3:
            risk_score += 2
        elif atr.get("percent", 0) > 2:
            risk_score += 1

        # Market cap
        market_cap = stock_info.get("market_cap", 0)
        if market_cap and market_cap < 1_000_000_000:
            risk_score += 2  # Small cap
        elif market_cap and market_cap < 10_000_000_000:
            risk_score += 1  # Mid cap

        # Sentiment volatility
        sentiment_score = factors.get("sentiment", {}).get("score", 0.5)
        if abs(sentiment_score - 0.5) > 0.3:
            risk_score += 1

        # Determine risk level
        if risk_score >= 4:
            return RiskLevel.VERY_HIGH
        elif risk_score >= 3:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _determine_time_horizon(
        self,
        technical_analysis: Dict[str, Any],
        factors: Dict[str, Any],
    ) -> TimeHorizon:
        """Determine appropriate time horizon."""
        # Check trend strength
        adx = technical_analysis.get("indicators", {}).get("trend", {}).get("adx", {})
        trend_strength = adx.get("trend_strength", "weak")

        if trend_strength == "strong":
            return TimeHorizon.LONG
        elif trend_strength == "moderate":
            return TimeHorizon.MEDIUM
        else:
            return TimeHorizon.SHORT

    def _calculate_price_targets(
        self,
        stock_info: Dict[str, Any],
        technical_analysis: Dict[str, Any],
        recommendation: RecommendationType,
    ) -> Dict[str, Optional[float]]:
        """Calculate price targets."""
        current_price = stock_info.get("current_price")
        if not current_price:
            return {"entry": None, "target": None, "stop_loss": None}

        # Get ATR for volatility-based targets
        atr = technical_analysis.get("indicators", {}).get("volatility", {}).get("atr", {})
        atr_value = current_price * atr.get("percent", 2) / 100

        # Get support/resistance from Bollinger Bands
        bb = technical_analysis.get("indicators", {}).get("volatility", {}).get("bollinger_bands", {})

        if recommendation == RecommendationType.BUY:
            entry = current_price
            target = current_price + (atr_value * 2)
            stop_loss = current_price - atr_value
        elif recommendation == RecommendationType.SELL:
            entry = current_price
            target = current_price - (atr_value * 2)
            stop_loss = current_price + atr_value
        else:
            entry = current_price
            target = current_price
            stop_loss = current_price - atr_value

        return {
            "entry": round(entry, 2),
            "target": round(target, 2),
            "stop_loss": round(stop_loss, 2),
        }

    async def _generate_reasoning(
        self,
        symbol: str,
        factors: Dict[str, Any],
        recommendation: RecommendationType,
        stock_info: Dict[str, Any],
    ) -> str:
        """Generate human-readable reasoning."""
        # Use Grok to generate reasoning
        try:
            result = await xai_grok_service.analyze_stock(
                symbol,
                stock_info,
            )
            return result.get("analysis", "Analysis not available")
        except Exception as e:
            logger.error(f"Error generating reasoning: {e}")
            # Fallback to simple reasoning
            return self._generate_simple_reasoning(factors, recommendation)

    def _generate_simple_reasoning(
        self,
        factors: Dict[str, Any],
        recommendation: RecommendationType,
    ) -> str:
        """Generate simple reasoning as fallback."""
        technical = factors.get("technical", {})
        fundamental = factors.get("fundamental", {})
        sentiment = factors.get("sentiment", {})

        reasoning_parts = []

        if technical.get("overall_signal") == "bullish":
            reasoning_parts.append("Technical indicators show bullish momentum")
        elif technical.get("overall_signal") == "bearish":
            reasoning_parts.append("Technical indicators show bearish momentum")

        if sentiment.get("overall_sentiment") == "positive":
            reasoning_parts.append("Market sentiment is positive")
        elif sentiment.get("overall_sentiment") == "negative":
            reasoning_parts.append("Market sentiment is negative")

        if recommendation == RecommendationType.BUY:
            reasoning_parts.append("Overall analysis suggests buying opportunity")
        elif recommendation == RecommendationType.SELL:
            reasoning_parts.append("Overall analysis suggests selling")
        else:
            reasoning_parts.append("Overall analysis suggests holding position")

        return ". ".join(reasoning_parts) + "."

    def _collect_citations(
        self,
        stock_info: Dict[str, Any],
        news_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Collect citations from data sources."""
        citations = []

        # Data source citation
        if stock_info.get("data_source"):
            citations.append({
                "source": stock_info["data_source"],
                "type": "market_data",
                "fetched_at": stock_info.get("fetched_at"),
            })

        # News citations
        for news in news_data.get("news", [])[:3]:
            citations.append({
                "source": news.get("source", "Unknown"),
                "url": news.get("url"),
                "title": news.get("title"),
                "published_at": news.get("published_at"),
            })

        return citations

    def _generate_disclaimers(
        self,
        recommendation: RecommendationType,
        risk_level: RiskLevel,
    ) -> List[str]:
        """Generate appropriate disclaimers."""
        disclaimers = [
            "This is not financial advice. Consult a professional before making investment decisions.",
            "Past performance does not guarantee future results.",
            "All investments carry risk, including potential loss of principal.",
        ]

        if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            disclaimers.append(
                "This recommendation involves high risk. Only invest what you can afford to lose."
            )

        if recommendation in [RecommendationType.BUY, RecommendationType.SELL]:
            disclaimers.append(
                "This is an informational analysis only, not a specific recommendation to trade."
            )

        return disclaimers


# Global engine instance
recommendation_engine = RecommendationEngine()
