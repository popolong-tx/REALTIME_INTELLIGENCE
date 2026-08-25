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
    reports = relationship(
        "IntelligenceReportArtifact",
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
    report = relationship(
        "IntelligenceReportArtifact",
        back_populates="run",
        uselist=False,
        cascade="all, delete-orphan",
    )


class IntelligenceReportArtifact(Base):
    """Immutable PDF artifact generated from one completed monitor run."""

    __tablename__ = "intelligence_report_artifacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    workspace_id = Column(String, nullable=False, index=True)
    monitor_id = Column(
        String,
        ForeignKey("intelligence_monitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id = Column(
        String,
        ForeignKey("intelligence_monitor_runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    workflow = Column(String, nullable=False, index=True)
    trigger = Column(String, nullable=False)
    source_request_id = Column(String, index=True)
    filename = Column(String, nullable=False)
    storage_path = Column(Text, nullable=False)
    content_type = Column(String, nullable=False, default="application/pdf")
    byte_size = Column(Integer, nullable=False)
    sha256 = Column(String, nullable=False)
    query_context = Column(JSON, nullable=False, default=dict)
    generated_at = Column(DateTime, nullable=False, default=utcnow_naive, index=True)

    monitor = relationship("IntelligenceMonitor", back_populates="reports")
    run = relationship("IntelligenceMonitorRun", back_populates="report")


class IntelligenceAnalysisRecord(Base):
    """Immutable snapshot of one usable intelligence analysis.

    The record deliberately does not cascade with a monitor. Removing a
    schedule must not erase the analysis that was produced while it existed.
    """

    __tablename__ = "intelligence_analysis_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    workspace_id = Column(String, nullable=False, index=True, default="personal")
    workflow = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False)
    trigger = Column(String, nullable=False, default="manual", index=True)
    monitor_id = Column(String, index=True)
    run_id = Column(String, unique=True, index=True)
    source_request_id = Column(String, index=True)
    query_context = Column(JSON, nullable=False, default=dict)
    result = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utcnow_naive, index=True)
