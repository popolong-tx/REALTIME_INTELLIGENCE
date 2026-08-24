"""Durable operational state for governance, webhooks, and saved plans."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text

from app.core.database import Base


def utcnow_naive() -> datetime:
    """Return UTC in the naive form expected by the local SQLite database."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuditEventRecord(Base):
    """Append-only audit event persisted across process restarts."""

    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    event_type = Column(String, nullable=False, index=True)
    user_id = Column(String, index=True)
    resource_type = Column(String, index=True)
    resource_id = Column(String, index=True)
    action = Column(String, nullable=False, default="")
    details = Column(JSON, nullable=False, default=dict)
    ip_address = Column(String)
    user_agent = Column(String)
    timestamp = Column(DateTime, nullable=False, default=utcnow_naive, index=True)


class WebhookConfigRecord(Base):
    """Persistent outbound webhook configuration."""

    __tablename__ = "webhook_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    workspace_id = Column(String, nullable=False, default="personal", index=True)
    name = Column(String, nullable=False)
    url = Column(Text, nullable=False)
    events = Column(JSON, nullable=False, default=list)
    secret = Column(Text)
    headers = Column(JSON, nullable=False, default=dict)
    status = Column(String, nullable=False, default="active", index=True)
    created_at = Column(DateTime, nullable=False, default=utcnow_naive)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=utcnow_naive,
        onupdate=utcnow_naive,
    )


class WebhookEventRecord(Base):
    """Persistent record of an inbound event or outbound delivery attempt."""

    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    webhook_id = Column(String, nullable=False, default="system", index=True)
    event_type = Column(String, nullable=False, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    status = Column(String, nullable=False, default="pending", index=True)
    response_code = Column(Integer)
    response_body = Column(Text)
    attempt_count = Column(Integer, nullable=False, default=0)
    timestamp = Column(DateTime, nullable=False, default=utcnow_naive, index=True)
    completed_at = Column(DateTime)


class SavedTradingPlan(Base):
    """Workspace-scoped plan record used by the plan library and paper portfolio."""

    __tablename__ = "saved_trading_plans"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    workspace_id = Column(String, nullable=False, default="personal", index=True)
    symbol = Column(String, nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    version = Column(String, nullable=False)
    status = Column(String, nullable=False, default="draft", index=True)
    evidence_status = Column(String, nullable=False, default="partial")
    user_plan = Column(JSON, nullable=False, default=dict)
    generated_plan = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=utcnow_naive, index=True)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=utcnow_naive,
        onupdate=utcnow_naive,
    )


class SystemControlState(Base):
    """Singleton execution gate for emergency shutdown state."""

    __tablename__ = "system_control_state"

    id = Column(String, primary_key=True, default="global")
    status = Column(String, nullable=False, default="active", index=True)
    current_shutdown = Column(JSON)
    updated_at = Column(DateTime, nullable=False, default=utcnow_naive)


class EmergencyShutdownRecord(Base):
    """Persistent history for shutdown and recovery actions."""

    __tablename__ = "emergency_shutdown_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    reason = Column(String, nullable=False)
    initiated_by = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    affected_systems = Column(JSON, nullable=False, default=lambda: ["all"])
    status = Column(String, nullable=False, default="active", index=True)
    initiated_at = Column(DateTime, nullable=False, default=utcnow_naive)
    recovery_initiated_by = Column(String)
    recovery_initiated_at = Column(DateTime)
    verification_checks = Column(JSON)
    resolved_by = Column(String)
    resolved_at = Column(DateTime)
