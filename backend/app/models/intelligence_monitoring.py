"""Persistent schedules and execution history for intelligence monitoring."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def utcnow_naive() -> datetime:
    """Return explicit UTC in SQLite-compatible naive form."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class IntelligenceMonitor(Base):
    """Workspace-scoped schedule for a governed intelligence workflow."""

    __tablename__ = "intelligence_monitors"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    workspace_id = Column(String, nullable=False, index=True, default="personal")
    monitor_type = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    schedule_minutes = Column(Integer, nullable=False)
    request_payload = Column(JSON, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    last_status = Column(String, nullable=False, default="scheduled")
    last_error = Column(Text)
    last_result = Column(JSON)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime, index=True)

    created_at = Column(DateTime, nullable=False, default=utcnow_naive)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=utcnow_naive,
        onupdate=utcnow_naive,
    )

    runs = relationship(
        "IntelligenceMonitorRun",
        back_populates="monitor",
        cascade="all, delete-orphan",
    )


class IntelligenceMonitorRun(Base):
    """Immutable record of one scheduled or user-triggered monitor execution."""

    __tablename__ = "intelligence_monitor_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    monitor_id = Column(
        String,
        ForeignKey("intelligence_monitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trigger = Column(String, nullable=False, default="schedule")
    status = Column(String, nullable=False, default="running")
    result = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime, nullable=False, default=utcnow_naive)
    completed_at = Column(DateTime)

    monitor = relationship("IntelligenceMonitor", back_populates="runs")
