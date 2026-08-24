from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from enum import Enum
import logging

from app.core.database import SessionLocal
from app.models.platform_operations import AuditEventRecord, utcnow_naive

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    MODEL_TRAINING = "model_training"
    MODEL_APPROVAL = "model_approval"
    MODEL_REJECTION = "model_rejection"
    MODEL_DEPLOYMENT = "model_deployment"
    RECOMMENDATION_GENERATED = "recommendation_generated"
    RECOMMENDATION_EXPIRED = "recommendation_expired"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    CONFIG_CHANGE = "config_change"
    DATA_ACCESS = "data_access"
    SYSTEM_EVENT = "system_event"


class AuditTrailService:
    """Store and query append-only audit events in the database."""

    @staticmethod
    def _serialize(record: AuditEventRecord) -> Dict[str, Any]:
        timestamp = record.timestamp.replace(tzinfo=timezone.utc)
        return {
            "id": record.id,
            "event_type": record.event_type,
            "user_id": record.user_id,
            "resource_type": record.resource_type,
            "resource_id": record.resource_id,
            "action": record.action,
            "details": record.details or {},
            "ip_address": record.ip_address,
            "user_agent": record.user_agent,
            "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        }

    @staticmethod
    def _naive_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    async def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: str = "",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log an audit event."""
        record = AuditEventRecord(
            event_type=event_type.value,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=utcnow_naive(),
        )
        with SessionLocal() as db:
            db.add(record)
            db.commit()
            db.refresh(record)
            event = self._serialize(record)

        logger.info("Audit: %s - %s by %s", event_type.value, action, user_id)
        return event

    async def log_model_training(
        self,
        model_id: str,
        user_id: str,
        details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Log model training event."""
        return await self.log_event(
            event_type=AuditEventType.MODEL_TRAINING,
            user_id=user_id,
            resource_type="model",
            resource_id=model_id,
            action="train_model",
            details=details,
        )

    async def log_model_approval(
        self,
        model_id: str,
        approved_by: str,
        action: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log model approval/rejection event."""
        event_type = (
            AuditEventType.MODEL_APPROVAL if action == "approve"
            else AuditEventType.MODEL_REJECTION
        )

        return await self.log_event(
            event_type=event_type,
            user_id=approved_by,
            resource_type="model",
            resource_id=model_id,
            action=action,
            details={"notes": notes},
        )

    async def log_model_deployment(
        self,
        model_id: str,
        deployed_by: str,
        environment: str,
        alias: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log model deployment event."""
        return await self.log_event(
            event_type=AuditEventType.MODEL_DEPLOYMENT,
            user_id=deployed_by,
            resource_type="model",
            resource_id=model_id,
            action="deploy_model",
            details={
                "environment": environment,
                "alias": alias,
            },
        )

    async def log_recommendation(
        self,
        recommendation_id: str,
        symbol: str,
        user_id: Optional[str] = None,
        recommendation_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log recommendation generation."""
        return await self.log_event(
            event_type=AuditEventType.RECOMMENDATION_GENERATED,
            user_id=user_id,
            resource_type="recommendation",
            resource_id=recommendation_id,
            action="generate_recommendation",
            details={
                "symbol": symbol,
                "recommendation_type": recommendation_type,
            },
        )

    async def log_config_change(
        self,
        user_id: str,
        config_type: str,
        changes: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Log configuration change."""
        return await self.log_event(
            event_type=AuditEventType.CONFIG_CHANGE,
            user_id=user_id,
            resource_type="config",
            action="update_config",
            details={
                "config_type": config_type,
                "changes": changes,
            },
        )

    async def log_data_access(
        self,
        user_id: str,
        data_type: str,
        symbol: Optional[str] = None,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log data access event."""
        return await self.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            resource_type="data",
            action="access_data",
            details={
                "data_type": data_type,
                "symbol": symbol,
                "query": query,
            },
        )

    async def get_audit_events(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get persisted audit events with filters."""
        with SessionLocal() as db:
            query = db.query(AuditEventRecord)
            if event_type:
                query = query.filter(AuditEventRecord.event_type == event_type.value)
            if user_id:
                query = query.filter(AuditEventRecord.user_id == user_id)
            if resource_type:
                query = query.filter(AuditEventRecord.resource_type == resource_type)
            if resource_id:
                query = query.filter(AuditEventRecord.resource_id == resource_id)
            if start_date:
                query = query.filter(AuditEventRecord.timestamp >= self._naive_utc(start_date))
            if end_date:
                query = query.filter(AuditEventRecord.timestamp <= self._naive_utc(end_date))
            total = query.count()
            records = (
                query.order_by(AuditEventRecord.timestamp.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            events = [self._serialize(record) for record in records]
        return {"events": events, "total": total, "limit": limit, "offset": offset}

    async def get_user_activity(
        self,
        user_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get user activity summary."""
        cutoff = utcnow_naive() - timedelta(days=days)
        with SessionLocal() as db:
            user_events = (
                db.query(AuditEventRecord)
                .filter(
                    AuditEventRecord.user_id == user_id,
                    AuditEventRecord.timestamp >= cutoff,
                )
                .all()
            )

        # Count by event type
        event_counts = {}
        for event in user_events:
            event_type = event.event_type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        return {
            "user_id": user_id,
            "total_events": len(user_events),
            "event_counts": event_counts,
            "period_days": days,
        }

    async def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
    ) -> List[Dict[str, Any]]:
        """Get history for a specific resource."""
        with SessionLocal() as db:
            records = (
                db.query(AuditEventRecord)
                .filter(
                    AuditEventRecord.resource_type == resource_type,
                    AuditEventRecord.resource_id == resource_id,
                )
                .order_by(AuditEventRecord.timestamp.desc())
                .all()
            )
            return [self._serialize(record) for record in records]

    async def export_audit_trail(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "json",
    ) -> Dict[str, Any]:
        """Export audit trail."""
        with SessionLocal() as db:
            query = db.query(AuditEventRecord)
            if start_date:
                query = query.filter(AuditEventRecord.timestamp >= self._naive_utc(start_date))
            if end_date:
                query = query.filter(AuditEventRecord.timestamp <= self._naive_utc(end_date))
            records = query.order_by(AuditEventRecord.timestamp.asc()).all()
            events = [self._serialize(record) for record in records]

        return {
            "events": events,
            "total": len(events),
            "exported_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "format": format,
            "storage": "database",
        }

    async def get_audit_stats(self) -> Dict[str, Any]:
        """Get audit trail statistics."""
        with SessionLocal() as db:
            records = db.query(AuditEventRecord).all()
        total_events = len(records)

        # Count by event type
        event_counts = {}
        for event in records:
            event_type = event.event_type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        # Count by user
        user_counts = {}
        for event in records:
            user_id = event.user_id
            if user_id:
                user_counts[user_id] = user_counts.get(user_id, 0) + 1

        return {
            "total_events": total_events,
            "event_counts": event_counts,
            "unique_users": len(user_counts),
            "top_users": sorted(
                user_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10],
            "storage": "database",
        }


# Global service instance
audit_trail_service = AuditTrailService()
