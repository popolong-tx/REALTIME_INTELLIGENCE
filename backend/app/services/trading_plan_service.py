"""Persistent workspace plan library for simulated recommendations."""

from datetime import timezone
from typing import Any, Dict, List

from sqlalchemy import func

from app.core.database import SessionLocal
from app.models.platform_operations import SavedTradingPlan, utcnow_naive


class TradingPlanNotFoundError(LookupError):
    pass


class TradingPlanService:
    ALLOWED_STATUSES = {"draft", "frozen", "active", "completed", "cancelled"}

    @staticmethod
    def _iso(value):
        return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

    def serialize(self, record: SavedTradingPlan) -> Dict[str, Any]:
        """Return the stable plan-library contract consumed by the product shell."""
        return {
            "id": record.id,
            "workspace_id": record.workspace_id,
            "symbol": record.symbol,
            "version": record.version,
            "version_number": record.version_number,
            "createdAt": self._iso(record.created_at),
            "updatedAt": self._iso(record.updated_at),
            "status": record.status,
            "evidenceStatus": record.evidence_status,
            "userPlan": record.user_plan or {},
            "generatedPlan": record.generated_plan or {},
            "storage": "database",
        }

    def create_plan(
        self,
        *,
        workspace_id: str,
        symbol: str,
        evidence_status: str,
        user_plan: Dict[str, Any],
        generated_plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        normalized_symbol = symbol.strip().upper()
        with SessionLocal() as db:
            current_version = (
                db.query(func.max(SavedTradingPlan.version_number))
                .filter(
                    SavedTradingPlan.workspace_id == workspace_id,
                    SavedTradingPlan.symbol == normalized_symbol,
                )
                .scalar()
                or 0
            )
            version_number = current_version + 1
            record = SavedTradingPlan(
                workspace_id=workspace_id,
                symbol=normalized_symbol,
                version_number=version_number,
                version=f"v1.{version_number - 1}",
                status="draft",
                evidence_status=evidence_status,
                user_plan=user_plan,
                generated_plan=generated_plan,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return self.serialize(record)

    def list_plans(self, workspace_id: str = "personal") -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            records = (
                db.query(SavedTradingPlan)
                .filter(SavedTradingPlan.workspace_id == workspace_id)
                .order_by(SavedTradingPlan.created_at.desc())
                .all()
            )
            return [self.serialize(record) for record in records]

    def update_status(
        self,
        plan_id: str,
        status: str,
        workspace_id: str = "personal",
    ) -> Dict[str, Any]:
        if status not in self.ALLOWED_STATUSES:
            raise ValueError(f"Unsupported plan status: {status}")
        with SessionLocal() as db:
            record = (
                db.query(SavedTradingPlan)
                .filter(
                    SavedTradingPlan.id == plan_id,
                    SavedTradingPlan.workspace_id == workspace_id,
                )
                .first()
            )
            if not record:
                raise TradingPlanNotFoundError(plan_id)
            record.status = status
            record.updated_at = utcnow_naive()
            db.commit()
            db.refresh(record)
            return self.serialize(record)


trading_plan_service = TradingPlanService()
