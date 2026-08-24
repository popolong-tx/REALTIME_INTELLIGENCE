from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
import uuid

from app.core.database import SessionLocal
from app.core.cache import cache

logger = logging.getLogger(__name__)


class RecommendationHistory:
    """Recommendation history record."""

    def __init__(
        self,
        id: str,
        symbol: str,
        recommendation: str,
        confidence: float,
        risk_level: str,
        entry_price: Optional[float],
        target_price: Optional[float],
        stop_loss: Optional[float],
        factors: Dict[str, Any],
        created_at: datetime,
        actual_outcome: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.symbol = symbol
        self.recommendation = recommendation
        self.confidence = confidence
        self.risk_level = risk_level
        self.entry_price = entry_price
        self.target_price = target_price
        self.stop_loss = stop_loss
        self.factors = factors
        self.created_at = created_at
        self.actual_outcome = actual_outcome

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "entry_price": self.entry_price,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
            "factors": self.factors,
            "created_at": self.created_at.isoformat(),
            "actual_outcome": self.actual_outcome,
        }


class RecommendationHistoryService:
    """Service for managing recommendation history and performance tracking."""

    def __init__(self):
        # In-memory storage (would use database in production)
        self.recommendations: Dict[str, RecommendationHistory] = {}

    async def save_recommendation(
        self,
        symbol: str,
        recommendation: str,
        confidence: float,
        risk_level: str,
        entry_price: Optional[float] = None,
        target_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        factors: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Save a recommendation to history."""
        rec_id = str(uuid.uuid4())

        record = RecommendationHistory(
            id=rec_id,
            symbol=symbol,
            recommendation=recommendation,
            confidence=confidence,
            risk_level=risk_level,
            entry_price=entry_price,
            target_price=target_price,
            stop_loss=stop_loss,
            factors=factors or {},
            created_at=datetime.utcnow(),
        )

        self.recommendations[rec_id] = record

        return record.to_dict()

    async def get_recommendation_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get recommendation history."""
        # Filter by symbol if provided
        records = list(self.recommendations.values())
        if symbol:
            records = [r for r in records if r.symbol == symbol]

        # Sort by date (newest first)
        records.sort(key=lambda r: r.created_at, reverse=True)

        # Apply pagination
        paginated = records[offset:offset + limit]

        return {
            "recommendations": [r.to_dict() for r in paginated],
            "total": len(records),
            "limit": limit,
            "offset": offset,
        }

    async def update_outcome(
        self,
        recommendation_id: str,
        actual_price: float,
        actual_return: float,
        outcome: str,  # "profit", "loss", "breakeven"
    ) -> Dict[str, Any]:
        """Update recommendation with actual outcome."""
        if recommendation_id not in self.recommendations:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        record = self.recommendations[recommendation_id]
        record.actual_outcome = {
            "actual_price": actual_price,
            "actual_return": actual_return,
            "outcome": outcome,
            "updated_at": datetime.utcnow().isoformat(),
        }

        return record.to_dict()

    async def get_performance_stats(
        self,
        symbol: Optional[str] = None,
        days: int = 90,
    ) -> Dict[str, Any]:
        """Get performance statistics."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Filter records
        records = list(self.recommendations.values())
        if symbol:
            records = [r for r in records if r.symbol == symbol]
        records = [r for r in records if r.created_at >= cutoff]

        if not records:
            return {
                "total_recommendations": 0,
                "accuracy": 0,
                "average_return": 0,
                "win_rate": 0,
            }

        # Calculate stats
        total = len(records)
        with_outcome = [r for r in records if r.actual_outcome]

        if with_outcome:
            wins = sum(1 for r in with_outcome if r.actual_outcome.get("outcome") == "profit")
            losses = sum(1 for r in with_outcome if r.actual_outcome.get("outcome") == "loss")
            win_rate = wins / len(with_outcome) if with_outcome else 0

            returns = [r.actual_outcome.get("actual_return", 0) for r in with_outcome]
            avg_return = sum(returns) / len(returns) if returns else 0
        else:
            win_rate = 0
            avg_return = 0

        # By recommendation type
        buy_recs = [r for r in records if r.recommendation == "buy"]
        sell_recs = [r for r in records if r.recommendation == "sell"]
        hold_recs = [r for r in records if r.recommendation == "hold"]

        return {
            "total_recommendations": total,
            "with_outcome": len(with_outcome),
            "win_rate": round(win_rate, 4),
            "average_return": round(avg_return, 4),
            "by_recommendation": {
                "buy": len(buy_recs),
                "sell": len(sell_recs),
                "hold": len(hold_recs),
            },
            "by_confidence": {
                "high": sum(1 for r in records if r.confidence >= 0.8),
                "medium": sum(1 for r in records if 0.6 <= r.confidence < 0.8),
                "low": sum(1 for r in records if r.confidence < 0.6),
            },
            "period_days": days,
        }

    async def get_symbol_performance(
        self,
        symbol: str,
    ) -> Dict[str, Any]:
        """Get performance for a specific symbol."""
        records = [r for r in self.recommendations.values() if r.symbol == symbol]

        if not records:
            return {
                "symbol": symbol,
                "total_recommendations": 0,
            }

        with_outcome = [r for r in records if r.actual_outcome]

        if with_outcome:
            wins = sum(1 for r in with_outcome if r.actual_outcome.get("outcome") == "profit")
            win_rate = wins / len(with_outcome)
            returns = [r.actual_outcome.get("actual_return", 0) for r in with_outcome]
            avg_return = sum(returns) / len(returns)
        else:
            win_rate = 0
            avg_return = 0

        return {
            "symbol": symbol,
            "total_recommendations": len(records),
            "win_rate": round(win_rate, 4),
            "average_return": round(avg_return, 4),
            "latest_recommendation": records[0].to_dict() if records else None,
            "recommendations": [r.to_dict() for r in records[:10]],
        }


# Global service instance
recommendation_history_service = RecommendationHistoryService()
