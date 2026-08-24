from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
import logging

from app.core.config import settings
from app.core.database import (
    SessionLocal,
    check_cache_connection,
    check_db_connection,
)
from app.models.platform_operations import (
    EmergencyShutdownRecord,
    SystemControlState,
    utcnow_naive,
)

logger = logging.getLogger(__name__)


class ShutdownReason(str, Enum):
    SYSTEM_ERROR = "system_error"
    DATA_CORRUPTION = "data_corruption"
    SECURITY_BREACH = "security_breach"
    COMPLIANCE_VIOLATION = "compliance_violation"
    MODEL_FAILURE = "model_failure"
    MANUAL = "manual"
    MAINTENANCE = "maintenance"


class ShutdownStatus(str, Enum):
    ACTIVE = "active"
    SHUTDOWN = "shutdown"
    RECOVERING = "recovering"


class EmergencyShutdownService:
    """Durable execution gate for recommendation and model operations."""

    @staticmethod
    def _iso(value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _get_or_create_state(db) -> SystemControlState:
        state = db.query(SystemControlState).filter(SystemControlState.id == "global").first()
        if not state:
            state = SystemControlState(id="global", status=ShutdownStatus.ACTIVE.value)
            db.add(state)
            db.commit()
            db.refresh(state)
        return state

    def _serialize_record(self, record: EmergencyShutdownRecord) -> Dict[str, Any]:
        return {
            "id": record.id,
            "reason": record.reason,
            "initiated_by": record.initiated_by,
            "description": record.description,
            "affected_systems": record.affected_systems or ["all"],
            "initiated_at": self._iso(record.initiated_at),
            "status": record.status,
            "recovery_initiated_by": record.recovery_initiated_by,
            "recovery_initiated_at": self._iso(record.recovery_initiated_at),
            "verification_checks": record.verification_checks,
            "resolved_by": record.resolved_by,
            "resolved_at": self._iso(record.resolved_at),
        }

    async def initiate_shutdown(
        self,
        reason: ShutdownReason,
        initiated_by: str,
        description: str,
        affected_systems: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Initiate emergency shutdown."""
        with SessionLocal() as db:
            state = self._get_or_create_state(db)
            if state.status == ShutdownStatus.SHUTDOWN.value:
                raise ValueError("System is already in shutdown state")
            record = EmergencyShutdownRecord(
                reason=reason.value,
                initiated_by=initiated_by,
                description=description,
                affected_systems=affected_systems or ["all"],
                status="active",
                initiated_at=utcnow_naive(),
            )
            db.add(record)
            db.flush()
            shutdown_record = self._serialize_record(record)
            state.status = ShutdownStatus.SHUTDOWN.value
            state.current_shutdown = shutdown_record
            state.updated_at = utcnow_naive()
            db.commit()

        # Log shutdown event
        logger.critical(f"EMERGENCY SHUTDOWN initiated by {initiated_by}: {description}")

        return {
            "shutdown_id": shutdown_record["id"],
            "status": "shutdown",
            "reason": reason.value,
            "initiated_by": initiated_by,
            "initiated_at": shutdown_record["initiated_at"],
            "affected_systems": shutdown_record["affected_systems"],
            "message": "System has been shut down. All recommendation generation and model operations are suspended.",
        }

    async def check_shutdown_status(self) -> Dict[str, Any]:
        """Check if system is in shutdown state."""
        with SessionLocal() as db:
            state = self._get_or_create_state(db)
            return {
                "status": state.status,
                "is_shutdown": state.status != ShutdownStatus.ACTIVE.value,
                "current_shutdown": state.current_shutdown,
                "storage": "database",
            }

    async def is_operation_allowed(self, system: str) -> bool:
        """Return whether the named mutation class may execute."""
        with SessionLocal() as db:
            state = self._get_or_create_state(db)
            if state.status == ShutdownStatus.ACTIVE.value:
                return True
            current = state.current_shutdown or {}
            affected = current.get("affected_systems") or ["all"]
            return "all" not in affected and system not in affected

    async def initiate_recovery(
        self,
        initiated_by: str,
        verification_checks: Dict[str, bool],
    ) -> Dict[str, Any]:
        """Initiate system recovery after shutdown."""
        failed_checks = [
            check for check, passed in verification_checks.items()
            if not passed
        ]

        if failed_checks:
            raise ValueError(f"Recovery verification failed: {', '.join(failed_checks)}")

        with SessionLocal() as db:
            state = self._get_or_create_state(db)
            if state.status != ShutdownStatus.SHUTDOWN.value:
                raise ValueError("System is not in shutdown state")
            record_id = (state.current_shutdown or {}).get("id")
            record = db.query(EmergencyShutdownRecord).filter(
                EmergencyShutdownRecord.id == record_id
            ).first()
            now = utcnow_naive()
            state.status = ShutdownStatus.RECOVERING.value
            state.updated_at = now
            if record:
                record.recovery_initiated_by = initiated_by
                record.recovery_initiated_at = now
                record.verification_checks = verification_checks
                state.current_shutdown = self._serialize_record(record)
            db.commit()

        return {
            "status": "recovering",
            "initiated_by": initiated_by,
            "verification_checks": verification_checks,
            "message": "System recovery initiated. Mutations remain blocked until completion.",
        }

    async def complete_recovery(
        self,
        initiated_by: str,
    ) -> Dict[str, Any]:
        """Complete system recovery."""
        with SessionLocal() as db:
            state = self._get_or_create_state(db)
            if state.status != ShutdownStatus.RECOVERING.value:
                raise ValueError("System is not in recovery state")
            record_id = (state.current_shutdown or {}).get("id")
            record = db.query(EmergencyShutdownRecord).filter(
                EmergencyShutdownRecord.id == record_id
            ).first()
            now = utcnow_naive()
            if record:
                record.status = "resolved"
                record.resolved_by = initiated_by
                record.resolved_at = now
            state.status = ShutdownStatus.ACTIVE.value
            state.current_shutdown = None
            state.updated_at = now
            db.commit()

        logger.info(f"System recovery completed by {initiated_by}")

        return {
            "status": "active",
            "resolved_by": initiated_by,
            "resolved_at": self._iso(now),
            "message": "System has been restored to normal operation.",
        }

    async def get_shutdown_history(self) -> List[Dict[str, Any]]:
        """Get shutdown history."""
        with SessionLocal() as db:
            records = (
                db.query(EmergencyShutdownRecord)
                .order_by(EmergencyShutdownRecord.initiated_at.desc())
                .all()
            )
            return [self._serialize_record(record) for record in records]

    async def get_current_status(self) -> Dict[str, Any]:
        """Get current system status."""
        with SessionLocal() as db:
            state = self._get_or_create_state(db)
            total = db.query(EmergencyShutdownRecord).count()
            return {
                "status": state.status,
                "is_operational": state.status == ShutdownStatus.ACTIVE.value,
                "current_shutdown": state.current_shutdown,
                "total_shutdowns": total,
                "storage": "database",
            }

    async def check_system_health(self) -> Dict[str, Any]:
        """Check system health and determine if shutdown is needed."""
        checks = {
            "database": check_db_connection(),
            "cache": check_cache_connection(),
            "market_data_adapter": bool(settings.YAHOO_FINANCE_ENABLED),
            "model_services": True,
        }
        return {
            "healthy": all(checks.values()),
            "checks": checks,
            "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

    async def emergency_stop_recommendations(self) -> Dict[str, Any]:
        """Emergency stop all recommendation generation."""
        if await self.is_operation_allowed("recommendations"):
            raise ValueError("Recommendation operations are not currently stopped")
        return {
            "recommendations_stopped": True,
            "stopped_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "message": "All recommendation generation has been stopped.",
        }

    async def emergency_stop_models(self) -> Dict[str, Any]:
        """Emergency stop all model operations."""
        if await self.is_operation_allowed("models"):
            raise ValueError("Model operations are not currently stopped")
        return {
            "models_stopped": True,
            "stopped_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "message": "All model operations have been stopped.",
        }


# Global service instance
emergency_shutdown_service = EmergencyShutdownService()
