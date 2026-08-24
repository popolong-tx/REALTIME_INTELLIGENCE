from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
import logging

from app.services.recommendation_engine import recommendation_engine
from app.services.stock_info_service import stock_info_service

logger = logging.getLogger(__name__)


class ExpirationReason(str, Enum):
    TIME_EXPIRED = "time_expired"
    PRICE_REACHED = "price_reached"
    STOP_LOSS_TRIGGERED = "stop_loss_triggered"
    TAKE_PROFIT_REACHED = "take_profit_reached"
    MARKET_CONDITION_CHANGED = "market_condition_changed"
    FUNDAMENTAL_CHANGED = "fundamental_changed"
    MANUAL_INVALIDATION = "manual_invalidation"


class RecommendationStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    TRIGGERED = "triggered"
    INVALIDATED = "invalidated"


class RecommendationExpirationService:
    """Service for managing recommendation expiration and re-evaluation."""

    def __init__(self):
        # In-memory storage (would use database in production)
        self.active_recommendations: Dict[str, Dict[str, Any]] = {}

    async def register_recommendation(
        self,
        recommendation_id: str,
        symbol: str,
        recommendation: Dict[str, Any],
        validity_days: int = 30,
    ) -> Dict[str, Any]:
        """Register a recommendation for expiration tracking."""
        expiration_date = datetime.utcnow() + timedelta(days=validity_days)

        self.active_recommendations[recommendation_id] = {
            "id": recommendation_id,
            "symbol": symbol,
            "recommendation": recommendation,
            "status": RecommendationStatus.ACTIVE.value,
            "registered_at": datetime.utcnow().isoformat(),
            "expires_at": expiration_date.isoformat(),
            "validity_days": validity_days,
            "last_checked": None,
            "expiration_reason": None,
        }

        return self.active_recommendations[recommendation_id]

    async def check_expiration(
        self,
        recommendation_id: str,
    ) -> Dict[str, Any]:
        """Check if a recommendation has expired."""
        if recommendation_id not in self.active_recommendations:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        rec = self.active_recommendations[recommendation_id]

        if rec["status"] != RecommendationStatus.ACTIVE.value:
            return rec

        # Check time expiration
        expires_at = datetime.fromisoformat(rec["expires_at"])
        if datetime.utcnow() > expires_at:
            rec["status"] = RecommendationStatus.EXPIRED.value
            rec["expiration_reason"] = ExpirationReason.TIME_EXPIRED.value
            return rec

        # Check price conditions
        symbol = rec["symbol"]
        recommendation = rec["recommendation"]

        try:
            stock_info = await stock_info_service.get_stock_overview(symbol)
            current_price = stock_info.get("current_price")

            if current_price:
                # Check stop loss
                stop_loss = recommendation.get("stop_loss")
                if stop_loss and current_price <= stop_loss:
                    rec["status"] = RecommendationStatus.TRIGGERED.value
                    rec["expiration_reason"] = ExpirationReason.STOP_LOSS_TRIGGERED.value
                    rec["triggered_at"] = datetime.utcnow().isoformat()
                    rec["triggered_price"] = current_price
                    return rec

                # Check take profit
                target_price = recommendation.get("target_price")
                if target_price and current_price >= target_price:
                    rec["status"] = RecommendationStatus.TRIGGERED.value
                    rec["expiration_reason"] = ExpirationReason.TAKE_PROFIT_REACHED.value
                    rec["triggered_at"] = datetime.utcnow().isoformat()
                    rec["triggered_price"] = current_price
                    return rec

            rec["last_checked"] = datetime.utcnow().isoformat()

        except Exception as e:
            logger.error(f"Error checking expiration for {recommendation_id}: {e}")

        return rec

    async def re_evaluate_recommendation(
        self,
        recommendation_id: str,
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Re-evaluate a recommendation based on current market conditions."""
        if recommendation_id not in self.active_recommendations:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        rec = self.active_recommendations[recommendation_id]
        symbol = rec["symbol"]

        try:
            # Generate new recommendation
            new_recommendation = await recommendation_engine.generate_recommendation(
                symbol, user_profile
            )

            # Compare with original
            original = rec["recommendation"]
            new_rec = new_recommendation.to_dict()

            # Check if recommendation changed significantly
            changed = self._has_significant_change(original, new_rec)

            result = {
                "recommendation_id": recommendation_id,
                "symbol": symbol,
                "original_recommendation": original,
                "new_recommendation": new_rec,
                "changed": changed,
                "re_evaluated_at": datetime.utcnow().isoformat(),
            }

            if changed:
                # Update recommendation
                rec["recommendation"] = new_rec
                rec["last_re_evaluation"] = datetime.utcnow().isoformat()
                result["action"] = "recommendation_updated"
            else:
                result["action"] = "no_change"

            return result

        except Exception as e:
            logger.error(f"Error re-evaluating recommendation {recommendation_id}: {e}")
            raise

    async def invalidate_recommendation(
        self,
        recommendation_id: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Manually invalidate a recommendation."""
        if recommendation_id not in self.active_recommendations:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        rec = self.active_recommendations[recommendation_id]
        rec["status"] = RecommendationStatus.INVALIDATED.value
        rec["expiration_reason"] = ExpirationReason.MANUAL_INVALIDATION.value
        rec["invalidation_reason"] = reason
        rec["invalidated_at"] = datetime.utcnow().isoformat()

        return rec

    async def get_active_recommendations(
        self,
        symbol: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all active recommendations."""
        active = [
            rec for rec in self.active_recommendations.values()
            if rec["status"] == RecommendationStatus.ACTIVE.value
        ]

        if symbol:
            active = [rec for rec in active if rec["symbol"] == symbol]

        return active

    async def get_expiring_recommendations(
        self,
        days: int = 7,
    ) -> List[Dict[str, Any]]:
        """Get recommendations expiring soon."""
        cutoff = datetime.utcnow() + timedelta(days=days)

        expiring = []
        for rec in self.active_recommendations.values():
            if rec["status"] == RecommendationStatus.ACTIVE.value:
                expires_at = datetime.fromisoformat(rec["expires_at"])
                if expires_at <= cutoff:
                    expiring.append(rec)

        return expiring

    def _has_significant_change(
        self,
        original: Dict[str, Any],
        new: Dict[str, Any],
    ) -> bool:
        """Check if recommendation has changed significantly."""
        # Check recommendation type
        if original.get("recommendation") != new.get("recommendation"):
            return True

        # Check confidence change
        orig_confidence = original.get("confidence", 0)
        new_confidence = new.get("confidence", 0)
        if abs(orig_confidence - new_confidence) > 0.2:
            return True

        # Check price target change
        orig_target = original.get("target_price")
        new_target = new.get("target_price")
        if orig_target and new_target:
            if abs(orig_target - new_target) / orig_target > 0.1:
                return True

        return False


# Global service instance
recommendation_expiration_service = RecommendationExpirationService()
