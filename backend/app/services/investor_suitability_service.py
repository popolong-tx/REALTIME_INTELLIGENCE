from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SuitabilityLevel(str, Enum):
    SUITABLE = "suitable"
    CAUTION = "caution"
    NOT_SUITABLE = "not_suitable"


class InvestorSuitabilityService:
    """Service for investor suitability checks."""

    def check_recommendation_suitability(
        self,
        user_profile: Dict[str, Any],
        recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check if a recommendation is suitable for an investor."""
        issues = []
        warnings = []

        # Check risk tolerance compatibility
        risk_check = self._check_risk_compatibility(user_profile, recommendation)
        if not risk_check["compatible"]:
            issues.extend(risk_check["issues"])
        warnings.extend(risk_check.get("warnings", []))

        # Check investment horizon compatibility
        horizon_check = self._check_horizon_compatibility(user_profile, recommendation)
        if not horizon_check["compatible"]:
            issues.extend(horizon_check["issues"])
        warnings.extend(horizon_check.get("warnings", []))

        # Check capital requirements
        capital_check = self._check_capital_requirements(user_profile, recommendation)
        if not capital_check["compatible"]:
            issues.extend(capital_check["issues"])
        warnings.extend(capital_check.get("warnings", []))

        # Check sector preferences
        sector_check = self._check_sector_preferences(user_profile, recommendation)
        warnings.extend(sector_check.get("warnings", []))

        # Determine suitability level
        if issues:
            level = SuitabilityLevel.NOT_SUITABLE
        elif warnings:
            level = SuitabilityLevel.CAUTION
        else:
            level = SuitabilityLevel.SUITABLE

        return {
            "suitable": level == SuitabilityLevel.SUITABLE,
            "level": level.value,
            "issues": issues,
            "warnings": warnings,
            "recommendation": recommendation.get("symbol"),
            "user_risk_tolerance": user_profile.get("risk_tolerance"),
            "recommendation_risk": recommendation.get("risk_level"),
        }

    def check_portfolio_suitability(
        self,
        user_profile: Dict[str, Any],
        portfolio: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check if a portfolio is suitable for an investor."""
        issues = []
        warnings = []

        # Check overall risk level
        portfolio_risk = portfolio.get("risk_score", 0)
        user_risk_tolerance = user_profile.get("risk_tolerance", "moderate")

        risk_levels = {"conservative": 0.3, "moderate": 0.6, "aggressive": 1.0}
        max_risk = risk_levels.get(user_risk_tolerance, 0.6)

        if portfolio_risk > max_risk:
            issues.append(f"投资组合风险 ({portfolio_risk:.0%}) 超出您的风险承受能力 ({user_risk_tolerance})")

        # Check diversification
        stock_count = portfolio.get("stock_count", 0)
        if stock_count < 3:
            warnings.append("投资组合分散度不足，建议增加更多股票")

        # Check position concentration
        max_allocation = portfolio.get("max_allocation", 0)
        if max_allocation > 0.3:
            warnings.append("单一持仓过于集中，建议降低最大持仓比例")

        # Determine suitability level
        if issues:
            level = SuitabilityLevel.NOT_SUITABLE
        elif warnings:
            level = SuitabilityLevel.CAUTION
        else:
            level = SuitabilityLevel.SUITABLE

        return {
            "suitable": level == SuitabilityLevel.SUITABLE,
            "level": level.value,
            "issues": issues,
            "warnings": warnings,
            "portfolio_risk": portfolio_risk,
            "user_risk_tolerance": user_risk_tolerance,
        }

    def _check_risk_compatibility(
        self,
        user_profile: Dict[str, Any],
        recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check risk compatibility."""
        issues = []
        warnings = []

        user_risk = user_profile.get("risk_tolerance", "moderate")
        rec_risk = recommendation.get("risk_level", "medium")

        # Risk compatibility matrix
        risk_matrix = {
            "conservative": ["low", "medium"],
            "moderate": ["low", "medium", "high"],
            "aggressive": ["low", "medium", "high", "very_high"],
        }

        allowed_risks = risk_matrix.get(user_risk, ["low", "medium"])

        if rec_risk not in allowed_risks:
            issues.append(
                f"推荐风险等级 ({rec_risk}) 不适合您的风险承受能力 ({user_risk})"
            )

        # Warnings for borderline cases
        if user_risk == "conservative" and rec_risk == "medium":
            warnings.append("该推荐风险处于您承受能力的上限，请谨慎考虑")

        return {
            "compatible": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }

    def _check_horizon_compatibility(
        self,
        user_profile: Dict[str, Any],
        recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check investment horizon compatibility."""
        issues = []
        warnings = []

        user_horizon = user_profile.get("investment_horizon", "medium")
        rec_horizon = recommendation.get("time_horizon", "medium")

        # Horizon compatibility
        horizon_days = {
            "short": 30,
            "medium": 90,
            "long": 365,
        }

        user_days = horizon_days.get(user_horizon, 90)
        rec_days = horizon_days.get(rec_horizon, 90)

        if rec_days > user_days * 2:
            issues.append(
                f"推荐投资期限 ({rec_horizon}) 远超您的投资期限 ({user_horizon})"
            )
        elif rec_days > user_days:
            warnings.append(
                f"推荐投资期限 ({rec_horizon}) 长于您的投资期限 ({user_horizon})"
            )

        return {
            "compatible": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }

    def _check_capital_requirements(
        self,
        user_profile: Dict[str, Any],
        recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check capital requirements."""
        issues = []
        warnings = []

        available_capital = user_profile.get("available_capital", 0)
        entry_price = recommendation.get("entry_price", 0)

        if entry_price and available_capital:
            # Check if minimum investment is feasible
            min_shares = 1
            min_investment = entry_price * min_shares

            if min_investment > available_capital * 0.5:
                issues.append("可用资金不足以进行有效投资")

            # Check position sizing
            max_position_pct = user_profile.get("max_position_size", 20) / 100
            max_position_value = available_capital * max_position_pct

            if entry_price > max_position_value:
                warnings.append("单股价格接近或超过最大仓位限制")

        return {
            "compatible": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }

    def _check_sector_preferences(
        self,
        user_profile: Dict[str, Any],
        recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check sector preferences."""
        warnings = []

        sector = recommendation.get("sector")
        if not sector:
            return {"warnings": warnings}

        excluded_sectors = user_profile.get("excluded_sectors", [])
        preferred_sectors = user_profile.get("preferred_sectors", [])

        if sector in excluded_sectors:
            warnings.append(f"该股票所在行业 ({sector}) 在您的排除列表中")

        if preferred_sectors and sector not in preferred_sectors:
            warnings.append(f"该股票所在行业 ({sector}) 不在您的偏好行业中")

        return {"warnings": warnings}

    def get_suitability_summary(
        self,
        user_profile: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Get suitability summary for multiple recommendations."""
        results = []
        suitable_count = 0
        caution_count = 0
        not_suitable_count = 0

        for rec in recommendations:
            check = self.check_recommendation_suitability(user_profile, rec)
            results.append({
                "symbol": rec.get("symbol"),
                "suitability": check["level"],
                "issues": check["issues"],
                "warnings": check["warnings"],
            })

            if check["level"] == SuitabilityLevel.SUITABLE.value:
                suitable_count += 1
            elif check["level"] == SuitabilityLevel.CAUTION.value:
                caution_count += 1
            else:
                not_suitable_count += 1

        return {
            "total": len(recommendations),
            "suitable": suitable_count,
            "caution": caution_count,
            "not_suitable": not_suitable_count,
            "results": results,
        }


# Global service instance
investor_suitability_service = InvestorSuitabilityService()
