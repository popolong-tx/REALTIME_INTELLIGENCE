from typing import Optional, Dict, Any, List
from datetime import datetime
import numpy as np
import logging

from app.services.recommendation_engine import recommendation_engine, RecommendationType
from app.services.single_stock_recommendation import single_stock_recommendation_service
from app.core.cache import cache

logger = logging.getLogger(__name__)


class PortfolioRecommendation:
    """Portfolio recommendation with allocation suggestions."""

    def __init__(
        self,
        stocks: List[Dict[str, Any]],
        total_allocation: float,
        risk_score: float,
        expected_return: float,
        diversification_score: float,
        rebalancing_suggestions: List[Dict[str, Any]],
    ):
        self.stocks = stocks
        self.total_allocation = total_allocation
        self.risk_score = risk_score
        self.expected_return = expected_return
        self.diversification_score = diversification_score
        self.rebalancing_suggestions = rebalancing_suggestions
        self.generated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stocks": self.stocks,
            "total_allocation": self.total_allocation,
            "risk_score": self.risk_score,
            "expected_return": self.expected_return,
            "diversification_score": self.diversification_score,
            "rebalancing_suggestions": self.rebalancing_suggestions,
            "generated_at": self.generated_at.isoformat(),
        }


class PortfolioRecommendationService:
    """Service for generating portfolio recommendations."""

    async def get_portfolio_recommendation(
        self,
        symbols: List[str],
        user_profile: Optional[Dict[str, Any]] = None,
        current_portfolio: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Get portfolio recommendation for multiple stocks."""
        try:
            # Get recommendations for all stocks
            recommendations = []
            for symbol in symbols:
                try:
                    rec = await single_stock_recommendation_service.get_quick_recommendation(symbol)
                    recommendations.append(rec)
                except Exception as e:
                    logger.error(f"Error getting recommendation for {symbol}: {e}")
                    continue

            if not recommendations:
                raise ValueError("No valid recommendations available")

            # Calculate optimal allocation
            allocations = self._calculate_optimal_allocation(
                recommendations, user_profile
            )

            # Calculate portfolio metrics
            portfolio_metrics = self._calculate_portfolio_metrics(
                recommendations, allocations
            )

            # Generate rebalancing suggestions
            rebalancing = self._generate_rebalancing_suggestions(
                allocations, current_portfolio
            )

            # Build stock recommendations with allocations
            stocks = []
            for rec, allocation in zip(recommendations, allocations):
                stocks.append({
                    "symbol": rec["symbol"],
                    "recommendation": rec["recommendation"],
                    "confidence": rec["confidence"],
                    "risk_level": rec["risk_level"],
                    "allocation": allocation,
                    "target_price": rec.get("target_price"),
                    "stop_loss": rec.get("stop_loss"),
                })

            return {
                "stocks": stocks,
                "portfolio_metrics": portfolio_metrics,
                "rebalancing_suggestions": rebalancing,
                "total_stocks": len(stocks),
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating portfolio recommendation: {e}")
            raise

    async def analyze_portfolio_risk(
        self,
        portfolio: Dict[str, float],
    ) -> Dict[str, Any]:
        """Analyze risk of a portfolio."""
        try:
            # Get recommendations for portfolio stocks
            recommendations = []
            for symbol in portfolio.keys():
                try:
                    rec = await single_stock_recommendation_service.get_quick_recommendation(symbol)
                    recommendations.append(rec)
                except Exception as e:
                    logger.error(f"Error getting recommendation for {symbol}: {e}")
                    continue

            # Calculate risk metrics
            risk_scores = []
            for rec in recommendations:
                risk_level = rec.get("risk_level", "medium")
                if risk_level == "low":
                    risk_scores.append(0.25)
                elif risk_level == "medium":
                    risk_scores.append(0.5)
                elif risk_level == "high":
                    risk_scores.append(0.75)
                else:
                    risk_scores.append(1.0)

            # Weighted risk score
            weights = [portfolio.get(rec["symbol"], 0) for rec in recommendations]
            total_weight = sum(weights)
            if total_weight > 0:
                weighted_risk = sum(r * w for r, w in zip(risk_scores, weights)) / total_weight
            else:
                weighted_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.5

            # Diversification analysis
            sectors = {}
            for rec in recommendations:
                sector = rec.get("sector", "Unknown")
                sectors[sector] = sectors.get(sector, 0) + portfolio.get(rec["symbol"], 0)

            # Concentration risk
            max_allocation = max(portfolio.values()) if portfolio else 0
            concentration_risk = "high" if max_allocation > 0.3 else "medium" if max_allocation > 0.2 else "low"

            return {
                "portfolio": portfolio,
                "risk_score": weighted_risk,
                "risk_level": "high" if weighted_risk > 0.7 else "medium" if weighted_risk > 0.4 else "low",
                "concentration_risk": concentration_risk,
                "max_allocation": max_allocation,
                "sector_allocation": sectors,
                "diversification_score": 1 - (len(sectors) / len(portfolio)) if portfolio else 0,
                "recommendations": recommendations,
            }

        except Exception as e:
            logger.error(f"Error analyzing portfolio risk: {e}")
            raise

    def _calculate_optimal_allocation(
        self,
        recommendations: List[Dict[str, Any]],
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> List[float]:
        """Calculate optimal allocation for portfolio."""
        n = len(recommendations)
        if n == 0:
            return []

        # Get risk tolerance from user profile
        risk_tolerance = "medium"
        if user_profile:
            risk_tolerance = user_profile.get("risk_tolerance", "medium")

        # Score each stock
        scores = []
        for rec in recommendations:
            score = rec.get("confidence", 0.5)

            # Adjust by recommendation
            if rec.get("recommendation") == "buy":
                score *= 1.2
            elif rec.get("recommendation") == "sell":
                score *= 0.5

            # Adjust by risk
            risk_level = rec.get("risk_level", "medium")
            if risk_tolerance == "conservative":
                if risk_level in ["high", "very_high"]:
                    score *= 0.5
            elif risk_tolerance == "aggressive":
                if risk_level in ["high", "very_high"]:
                    score *= 1.2

            scores.append(score)

        # Normalize to percentages
        total_score = sum(scores)
        if total_score == 0:
            # Equal allocation
            return [1.0 / n] * n

        allocations = [s / total_score for s in scores]

        # Apply constraints
        max_allocation = 0.3 if risk_tolerance == "conservative" else 0.4
        min_allocation = 0.05

        # Clip allocations
        allocations = [max(min(a, max_allocation), min_allocation) for a in allocations]

        # Renormalize
        total = sum(allocations)
        allocations = [a / total for a in allocations]

        return allocations

    def _calculate_portfolio_metrics(
        self,
        recommendations: List[Dict[str, Any]],
        allocations: List[float],
    ) -> Dict[str, Any]:
        """Calculate portfolio-level metrics."""
        # Risk score
        risk_scores = []
        for rec in recommendations:
            risk_level = rec.get("risk_level", "medium")
            if risk_level == "low":
                risk_scores.append(0.25)
            elif risk_level == "medium":
                risk_scores.append(0.5)
            elif risk_level == "high":
                risk_scores.append(0.75)
            else:
                risk_scores.append(1.0)

        weighted_risk = sum(r * a for r, a in zip(risk_scores, allocations))

        # Expected return (simplified)
        expected_returns = []
        for rec in recommendations:
            if rec.get("recommendation") == "buy":
                expected_returns.append(0.15)
            elif rec.get("recommendation") == "hold":
                expected_returns.append(0.05)
            else:
                expected_returns.append(-0.05)

        weighted_return = sum(r * a for r, a in zip(expected_returns, allocations))

        # Diversification score
        unique_risk_levels = len(set(rec.get("risk_level") for rec in recommendations))
        diversification_score = min(unique_risk_levels / 3, 1.0)

        return {
            "risk_score": round(weighted_risk, 2),
            "risk_level": "high" if weighted_risk > 0.7 else "medium" if weighted_risk > 0.4 else "low",
            "expected_return": round(weighted_return, 4),
            "diversification_score": round(diversification_score, 2),
            "stock_count": len(recommendations),
        }

    def _generate_rebalancing_suggestions(
        self,
        target_allocations: List[float],
        current_portfolio: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate rebalancing suggestions."""
        suggestions = []

        if not current_portfolio:
            return suggestions

        # This would compare current vs target allocations
        # For now, return empty suggestions
        return suggestions


# Global service instance
portfolio_recommendation_service = PortfolioRecommendationService()
