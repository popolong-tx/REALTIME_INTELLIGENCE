from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class StopLossType(str, Enum):
    FIXED = "fixed"
    TRAILING = "trailing"
    ATR_BASED = "atr_based"
    PERCENTAGE = "percentage"


class RiskManagementService:
    """Service for risk management including stop-loss and position sizing."""

    def calculate_position_size(
        self,
        account_balance: float,
        risk_per_trade: float,
        entry_price: float,
        stop_loss_price: float,
        risk_tolerance: str = "medium",
    ) -> Dict[str, Any]:
        """Calculate position size based on risk parameters."""
        # Calculate risk amount
        risk_amount = account_balance * risk_per_trade

        # Calculate price risk
        price_risk = abs(entry_price - stop_loss_price)
        if price_risk == 0:
            price_risk = entry_price * 0.02  # Default 2% risk

        # Calculate position size
        position_size = risk_amount / price_risk
        position_value = position_size * entry_price

        # Apply position limits based on risk tolerance
        max_position_pct = self._get_max_position_pct(risk_tolerance)
        max_position_value = account_balance * max_position_pct

        if position_value > max_position_value:
            position_size = max_position_value / entry_price
            position_value = max_position_value

        return {
            "position_size": int(position_size),
            "position_value": round(position_value, 2),
            "risk_amount": round(risk_amount, 2),
            "risk_percentage": round(risk_per_trade * 100, 2),
            "price_risk": round(price_risk, 2),
            "risk_reward_ratio": round(price_risk / price_risk, 2) if price_risk > 0 else 0,
        }

    def calculate_stop_loss(
        self,
        entry_price: float,
        stop_loss_type: StopLossType = StopLossType.PERCENTAGE,
        percentage: float = 0.05,
        atr_value: Optional[float] = None,
        atr_multiplier: float = 2.0,
    ) -> Dict[str, Any]:
        """Calculate stop-loss price."""
        if stop_loss_type == StopLossType.PERCENTAGE:
            stop_loss = entry_price * (1 - percentage)
        elif stop_loss_type == StopLossType.ATR_BASED and atr_value:
            stop_loss = entry_price - (atr_value * atr_multiplier)
        elif stop_loss_type == StopLossType.FIXED:
            stop_loss = entry_price * 0.95  # Fixed 5% below
        else:
            stop_loss = entry_price * (1 - percentage)

        return {
            "stop_loss_price": round(stop_loss, 2),
            "stop_loss_type": stop_loss_type.value,
            "distance_percentage": round((entry_price - stop_loss) / entry_price * 100, 2),
            "risk_amount_per_share": round(entry_price - stop_loss, 2),
        }

    def calculate_take_profit(
        self,
        entry_price: float,
        stop_loss_price: float,
        risk_reward_ratio: float = 2.0,
    ) -> Dict[str, Any]:
        """Calculate take-profit price."""
        risk = entry_price - stop_loss_price
        take_profit = entry_price + (risk * risk_reward_ratio)

        return {
            "take_profit_price": round(take_profit, 2),
            "potential_profit": round(take_profit - entry_price, 2),
            "potential_profit_percentage": round((take_profit - entry_price) / entry_price * 100, 2),
            "risk_reward_ratio": risk_reward_ratio,
        }

    def calculate_trailing_stop(
        self,
        current_price: float,
        highest_price: float,
        trailing_percentage: float = 0.05,
    ) -> Dict[str, Any]:
        """Calculate trailing stop-loss."""
        trailing_stop = highest_price * (1 - trailing_percentage)

        # Ensure trailing stop is below current price
        if trailing_stop > current_price:
            trailing_stop = current_price * (1 - trailing_percentage)

        return {
            "trailing_stop_price": round(trailing_stop, 2),
            "highest_price": highest_price,
            "current_price": current_price,
            "trailing_percentage": trailing_percentage * 100,
            "distance_from_current": round((current_price - trailing_stop) / current_price * 100, 2),
        }

    def assess_portfolio_risk(
        self,
        positions: List[Dict[str, Any]],
        account_balance: float,
    ) -> Dict[str, Any]:
        """Assess overall portfolio risk."""
        if not positions:
            return {
                "total_risk": 0,
                "risk_level": RiskLevel.LOW,
                "positions": [],
            }

        total_position_value = sum(p.get("value", 0) for p in positions)
        total_risk = sum(p.get("risk", 0) for p in positions)

        # Concentration risk
        max_position = max(p.get("value", 0) for p in positions)
        concentration_pct = max_position / total_position_value if total_position_value > 0 else 0

        # Sector risk
        sectors = {}
        for p in positions:
            sector = p.get("sector", "Unknown")
            sectors[sector] = sectors.get(sector, 0) + p.get("value", 0)

        sector_concentration = max(sectors.values()) / total_position_value if sectors and total_position_value > 0 else 0

        # Determine risk level
        risk_score = 0
        if concentration_pct > 0.3:
            risk_score += 2
        elif concentration_pct > 0.2:
            risk_score += 1

        if sector_concentration > 0.5:
            risk_score += 2
        elif sector_concentration > 0.3:
            risk_score += 1

        if total_risk / account_balance > 0.1:
            risk_score += 2
        elif total_risk / account_balance > 0.05:
            risk_score += 1

        if risk_score >= 4:
            risk_level = RiskLevel.VERY_HIGH
        elif risk_score >= 3:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 2:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return {
            "total_position_value": round(total_position_value, 2),
            "total_risk": round(total_risk, 2),
            "risk_percentage": round(total_risk / account_balance * 100, 2) if account_balance > 0 else 0,
            "concentration_risk": round(concentration_pct * 100, 2),
            "sector_concentration": round(sector_concentration * 100, 2),
            "risk_level": risk_level.value,
            "positions": positions,
            "recommendations": self._generate_risk_recommendations(
                risk_level, concentration_pct, sector_concentration
            ),
        }

    def _get_max_position_pct(self, risk_tolerance: str) -> float:
        """Get maximum position percentage based on risk tolerance."""
        if risk_tolerance == "conservative":
            return 0.15
        elif risk_tolerance == "aggressive":
            return 0.35
        else:
            return 0.25

    def _generate_risk_recommendations(
        self,
        risk_level: RiskLevel,
        concentration_pct: float,
        sector_concentration: float,
    ) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []

        if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            recommendations.append("考虑降低整体仓位以控制风险")

        if concentration_pct > 0.3:
            recommendations.append("单一持仓过于集中，建议分散投资")

        if sector_concentration > 0.5:
            recommendations.append("行业集中度过高，建议增加行业分散")

        if not recommendations:
            recommendations.append("当前风险水平可接受")

        return recommendations


# Global service instance
risk_management_service = RiskManagementService()
