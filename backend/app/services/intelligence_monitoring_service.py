"""Persistent interval scheduler for Grok intelligence workflows.

The local foundation runs one scheduler per application process. Production
multi-worker deployments should replace this loop with a distributed scheduler
and tenant-aware lease, while keeping the API and persistence contract stable.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.intelligence_monitoring import IntelligenceMonitor, IntelligenceMonitorRun
from app.services.audit_trail_service import AuditEventType, audit_trail_service
from app.services.institutional_intelligence_service import institutional_intelligence_service
from app.services.intelligence_report_artifact_service import (
    intelligence_report_artifact_service,
)
from app.services.intelligence_history_service import intelligence_history_service


logger = logging.getLogger(__name__)

SUPPORTED_INTERVAL_MINUTES = (30, 60, 120, 240, 360, 480, 720, 1440)
SUPPORTED_MONITOR_TYPES = ("realtime_research", "project_risk")
SCHEDULER_POLL_SECONDS = 30


class MonitorNotFoundError(LookupError):
    pass


class MonitorAlreadyRunningError(RuntimeError):
    pass


class IntelligenceMonitoringService:
    """Manage saved monitors and execute due Grok research tasks."""

    def __init__(self) -> None:
        self._scheduler_task: Optional[asyncio.Task] = None
        self._state_lock = asyncio.Lock()
        self._running_ids: set[str] = set()

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _iso(value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def interval_label(minutes: int) -> str:
        if minutes == 30:
            return "每 30 分钟"
        return f"每 {minutes // 60} 小时"

    def serialize_monitor(
        self,
        monitor: IntelligenceMonitor,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        latest_report = (
            intelligence_report_artifact_service.latest_for_monitor(db, monitor.id)
            if db is not None
            else None
        )
        return {
            "id": monitor.id,
            "workspace_id": monitor.workspace_id,
            "monitor_type": monitor.monitor_type,
            "name": monitor.name,
            "schedule_minutes": monitor.schedule_minutes,
            "schedule_label": self.interval_label(monitor.schedule_minutes),
            "request_payload": monitor.request_payload or {},
            "is_active": bool(monitor.is_active),
            "last_status": monitor.last_status,
            "last_error": monitor.last_error,
            "last_result": monitor.last_result,
            "last_run_at": self._iso(monitor.last_run_at),
            "next_run_at": self._iso(monitor.next_run_at),
            "created_at": self._iso(monitor.created_at),
            "updated_at": self._iso(monitor.updated_at),
            "latest_report": (
                intelligence_report_artifact_service.serialize(latest_report)
                if latest_report
                else None
            ),
        }

    def serialize_run(
        self,
        run: IntelligenceMonitorRun,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        report = (
            intelligence_report_artifact_service.for_run(db, run.id)
            if db is not None
            else None
        )
        return {
            "id": run.id,
            "monitor_id": run.monitor_id,
            "trigger": run.trigger,
            "status": run.status,
            "result": run.result,
            "error_message": run.error_message,
            "started_at": self._iso(run.started_at),
            "completed_at": self._iso(run.completed_at),
            "report": intelligence_report_artifact_service.serialize(report) if report else None,
        }

    def list_monitors(
        self,
        db: Session,
        workspace_id: str,
        monitor_type: Optional[str] = None,
    ) -> List[IntelligenceMonitor]:
        query = db.query(IntelligenceMonitor).filter(
            IntelligenceMonitor.workspace_id == workspace_id
        )
        if monitor_type:
            query = query.filter(IntelligenceMonitor.monitor_type == monitor_type)
        return query.order_by(IntelligenceMonitor.created_at.desc()).all()

    def get_monitor(
        self,
        db: Session,
        monitor_id: str,
        workspace_id: Optional[str] = None,
    ) -> IntelligenceMonitor:
        query = db.query(IntelligenceMonitor).filter(IntelligenceMonitor.id == monitor_id)
        if workspace_id is not None:
            query = query.filter(IntelligenceMonitor.workspace_id == workspace_id)
        monitor = query.first()
        if not monitor:
            raise MonitorNotFoundError(monitor_id)
        return monitor

    def create_monitor(
        self,
        db: Session,
        *,
        workspace_id: str,
        monitor_type: str,
        name: str,
        schedule_minutes: int,
        request_payload: Dict[str, Any],
        is_active: bool = True,
    ) -> IntelligenceMonitor:
        now = self._utcnow()
        monitor = IntelligenceMonitor(
            workspace_id=workspace_id,
            monitor_type=monitor_type,
            name=name,
            schedule_minutes=schedule_minutes,
            request_payload=request_payload,
            is_active=is_active,
            last_status="scheduled" if is_active else "paused",
            next_run_at=now + timedelta(minutes=schedule_minutes) if is_active else None,
        )
        db.add(monitor)
        db.commit()
        db.refresh(monitor)
        return monitor

    def update_monitor(
        self,
        db: Session,
        monitor_id: str,
        workspace_id: Optional[str] = None,
        *,
        name: Optional[str] = None,
        schedule_minutes: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> IntelligenceMonitor:
        monitor = self.get_monitor(db, monitor_id)
        now = self._utcnow()
        if name is not None:
            monitor.name = name
        if schedule_minutes is not None:
            monitor.schedule_minutes = schedule_minutes
        if is_active is not None:
            monitor.is_active = is_active
            monitor.last_status = "scheduled" if is_active else "paused"
        if monitor.is_active and (schedule_minutes is not None or is_active is True):
            monitor.next_run_at = now + timedelta(minutes=monitor.schedule_minutes)
        elif not monitor.is_active:
            monitor.next_run_at = None
        monitor.updated_at = now
        db.commit()
        db.refresh(monitor)
        return monitor

    def delete_monitor(self, db: Session, monitor_id: str) -> None:
        monitor = self.get_monitor(db, monitor_id)
        report_paths = intelligence_report_artifact_service.monitor_storage_paths(db, monitor_id)
        db.delete(monitor)
        db.commit()
        intelligence_report_artifact_service.delete_storage_paths(report_paths)

    def list_runs(
        self,
        db: Session,
        monitor_id: str,
        limit: int = 20,
    ) -> List[IntelligenceMonitorRun]:
        self.get_monitor(db, monitor_id, workspace_id=workspace_id)
        return (
            db.query(IntelligenceMonitorRun)
            .join(IntelligenceMonitor)
            .filter(
                IntelligenceMonitorRun.monitor_id == monitor_id,
                *([IntelligenceMonitor.workspace_id == workspace_id] if workspace_id else []),
            )
            .order_by(IntelligenceMonitorRun.started_at.desc())
            .limit(limit)
            .all()
        )

    async def execute_monitor(
        self,
        monitor_id: str,
        trigger: str = "manual",
        workspace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with self._state_lock:
            if monitor_id in self._running_ids:
                raise MonitorAlreadyRunningError(monitor_id)
            self._running_ids.add(monitor_id)

        run_id: Optional[str] = None
        try:
            with SessionLocal() as db:
                monitor = self.get_monitor(db, monitor_id, workspace_id=workspace_id)
                if trigger == "schedule" and not monitor.is_active:
                    return {"skipped": True, "reason": "monitor_paused"}
                run = IntelligenceMonitorRun(
                    monitor_id=monitor.id,
                    trigger=trigger,
                    status="running",
                    started_at=self._utcnow(),
                )
                monitor.last_status = "running"
                monitor.last_error = None
                db.add(run)
                db.commit()
                db.refresh(run)
                run_id = run.id
                monitor_type = monitor.monitor_type
                request_payload = dict(monitor.request_payload or {})

            if monitor_type == "realtime_research":
                result = await institutional_intelligence_service.search_realtime_information(
                    request_payload
                )
            elif monitor_type == "project_risk":
                result = await institutional_intelligence_service.analyze_project_risk(
                    request_payload
                )
            else:
                raise ValueError(f"Unsupported monitor type: {monitor_type}")

            completed_at = self._utcnow()
            result_status = str(result.get("status") or "completed")
            with SessionLocal() as db:
                monitor = self.get_monitor(db, monitor_id)
                run = (
                    db.query(IntelligenceMonitorRun)
                    .filter(IntelligenceMonitorRun.id == run_id)
                    .first()
                )
                if run:
                    run.status = result_status
                    run.result = result
                    run.completed_at = completed_at
                monitor.last_status = result_status
                monitor.last_result = result
                monitor.last_error = None
                monitor.last_run_at = completed_at
                monitor.next_run_at = (
                    completed_at + timedelta(minutes=monitor.schedule_minutes)
                    if monitor.is_active
                    else None
                )
                monitor.updated_at = completed_at
                db.commit()
                db.refresh(monitor)
                if run:
                    db.refresh(run)
                history_record = None
                history_error = None
                if run and result_status in {"live", "partial"}:
                    try:
                        workflow = (
                            "realtime-research"
                            if monitor.monitor_type == "realtime_research"
                            else "project-risk"
                        )
                        history_record = intelligence_history_service.save(
                            db,
                            workflow=workflow,
                            query_context=request_payload,
                            result=result,
                            trigger=trigger,
                            monitor_id=monitor.id,
                            run_id=run.id,
                        )
                    except Exception as exc:
                        history_error = str(exc)
                        logger.exception(
                            "Analysis history save failed for intelligence run %s",
                            run.id,
                        )
                    if history_record:
                        try:
                            await audit_trail_service.log_event(
                                event_type=AuditEventType.DATA_ACCESS,
                                user_id=monitor.workspace_id,
                                resource_type="intelligence_analysis_history",
                                resource_id=history_record.id,
                                action="save_analysis_history",
                                details={
                                    "monitor_id": monitor.id,
                                    "run_id": run.id,
                                    "trigger": trigger,
                                    "workflow": history_record.workflow,
                                    "source_request_id": history_record.source_request_id,
                                },
                            )
                        except Exception:
                            logger.exception(
                                "Analysis history audit failed for intelligence run %s",
                                run.id,
                            )
                report = None
                report_error = None
                if run and result_status in {"live", "partial"}:
                    try:
                        report = intelligence_report_artifact_service.create_for_run(
                            db,
                            monitor=monitor,
                            run=run,
                            result=result,
                            query_context=request_payload,
                        )
                    except Exception as exc:
                        report_error = str(exc)
                        logger.exception(
                            "Automatic PDF generation failed for intelligence run %s",
                            run.id,
                        )
                    if report:
                        try:
                            await audit_trail_service.log_event(
                                event_type=AuditEventType.DATA_ACCESS,
                                user_id=monitor.workspace_id,
                                resource_type="intelligence_report",
                                resource_id=report.id,
                                action="generate_monitor_pdf",
                                details={
                                    "monitor_id": monitor.id,
                                    "run_id": run.id,
                                    "trigger": trigger,
                                    "workflow": report.workflow,
                                    "source_request_id": report.source_request_id,
                                    "content_bytes": report.byte_size,
                                    "sha256": report.sha256,
                                    "template_version": "1.0",
                                },
                            )
                        except Exception:
                            logger.exception(
                                "Automatic PDF audit failed for intelligence run %s",
                                run.id,
                            )
                return {
                    "monitor": self.serialize_monitor(monitor, db),
                    "run": self.serialize_run(run, db) if run else None,
                    "report_generation": {
                        "status": "generated"
                        if report
                        else "failed"
                        if report_error
                        else "skipped",
                        "error": report_error,
                    },
                    "history_record": (
                        intelligence_history_service.serialize_summary(history_record)
                        if history_record
                        else None
                    ),
                    "history_save": {
                        "status": "saved"
                        if history_record
                        else "failed"
                        if history_error
                        else "skipped",
                        "error": history_error,
                    },
                }
        except Exception as exc:
            completed_at = self._utcnow()
            with SessionLocal() as db:
                monitor = (
                    db.query(IntelligenceMonitor)
                    .filter(IntelligenceMonitor.id == monitor_id)
                    .first()
                )
                run = (
                    db.query(IntelligenceMonitorRun)
                    .filter(IntelligenceMonitorRun.id == run_id)
                    .first()
                    if run_id
                    else None
                )
                if run:
                    run.status = "failed"
                    run.error_message = str(exc)
                    run.completed_at = completed_at
                if monitor:
                    monitor.last_status = "failed"
                    monitor.last_error = str(exc)
                    monitor.last_run_at = completed_at
                    monitor.next_run_at = (
                        completed_at + timedelta(minutes=monitor.schedule_minutes)
                        if monitor.is_active
                        else None
                    )
                    monitor.updated_at = completed_at
                db.commit()
            raise
        finally:
            async with self._state_lock:
                self._running_ids.discard(monitor_id)

    async def run_due_monitors(self) -> int:
        now = self._utcnow()
        with SessionLocal() as db:
            monitor_ids = [
                item.id
                for item in (
                    db.query(IntelligenceMonitor)
                    .filter(
                        IntelligenceMonitor.is_active.is_(True),
                        IntelligenceMonitor.next_run_at.isnot(None),
                        IntelligenceMonitor.next_run_at <= now,
                    )
                    .order_by(IntelligenceMonitor.next_run_at.asc())
                    .all()
                )
            ]
        executed = 0
        for monitor_id in monitor_ids:
            try:
                await self.execute_monitor(monitor_id, trigger="schedule")
                executed += 1
            except MonitorAlreadyRunningError:
                logger.info("Monitor %s is already running; skipping duplicate tick", monitor_id)
            except Exception:
                logger.exception("Scheduled intelligence monitor %s failed", monitor_id)
        return executed

    async def _scheduler_loop(self) -> None:
        logger.info(
            "Intelligence monitor scheduler started (poll=%ss, intervals=%s)",
            SCHEDULER_POLL_SECONDS,
            SUPPORTED_INTERVAL_MINUTES,
        )
        while True:
            try:
                await self.run_due_monitors()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Intelligence monitor scheduler tick failed")
            await asyncio.sleep(SCHEDULER_POLL_SECONDS)

    def start(self) -> None:
        if self._scheduler_task and not self._scheduler_task.done():
            return
        self._scheduler_task = asyncio.create_task(
            self._scheduler_loop(),
            name="intelligence-monitor-scheduler",
        )

    async def stop(self) -> None:
        if not self._scheduler_task:
            return
        self._scheduler_task.cancel()
        try:
            await self._scheduler_task
        except asyncio.CancelledError:
            pass
        self._scheduler_task = None

    def scheduler_status(self) -> Dict[str, Any]:
        return {
            "running": bool(self._scheduler_task and not self._scheduler_task.done()),
            "poll_seconds": SCHEDULER_POLL_SECONDS,
            "supported_interval_minutes": list(SUPPORTED_INTERVAL_MINUTES),
            "scope": "single_process_local_foundation",
        }


intelligence_monitoring_service = IntelligenceMonitoringService()
