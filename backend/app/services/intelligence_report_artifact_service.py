"""Durable PDF artifacts generated from completed intelligence monitor runs."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.intelligence_monitoring import (
    IntelligenceMonitor,
    IntelligenceMonitorRun,
    IntelligenceReportArtifact,
)
from app.services.intelligence_pdf_service import intelligence_pdf_service


MONITOR_WORKFLOWS = {
    "realtime_research": "realtime-research",
    "project_risk": "project-risk",
}


class ReportArtifactNotFoundError(LookupError):
    pass


class ReportArtifactStorageError(RuntimeError):
    pass


class IntelligenceReportArtifactService:
    """Write validated reports atomically and expose workspace-scoped metadata."""

    def __init__(self) -> None:
        self.reports_dir = Path(settings.INTELLIGENCE_REPORTS_DIR)

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _iso(value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def serialize(report: IntelligenceReportArtifact) -> Dict[str, Any]:
        return {
            "id": report.id,
            "workspace_id": report.workspace_id,
            "monitor_id": report.monitor_id,
            "run_id": report.run_id,
            "workflow": report.workflow,
            "trigger": report.trigger,
            "source_request_id": report.source_request_id,
            "filename": report.filename,
            "content_type": report.content_type,
            "byte_size": report.byte_size,
            "sha256": report.sha256,
            "generated_at": IntelligenceReportArtifactService._iso(report.generated_at),
        }

    def _artifact_path(self, workspace_id: str, monitor_id: str, run_id: str) -> Path:
        workspace_key = sha256(workspace_id.encode("utf-8")).hexdigest()[:20]
        return self.reports_dir / workspace_key / monitor_id / f"{run_id}.pdf"

    def create_for_run(
        self,
        db: Session,
        *,
        monitor: IntelligenceMonitor,
        run: IntelligenceMonitorRun,
        result: Dict[str, Any],
        query_context: Dict[str, Any],
    ) -> IntelligenceReportArtifact:
        existing = (
            db.query(IntelligenceReportArtifact)
            .filter(IntelligenceReportArtifact.run_id == run.id)
            .first()
        )
        if existing:
            return existing

        workflow = MONITOR_WORKFLOWS.get(monitor.monitor_type)
        if not workflow:
            raise ValueError(f"Unsupported monitor type: {monitor.monitor_type}")
        rendered = intelligence_pdf_service.generate(workflow, result, query_context)
        report_id = str(uuid4())
        final_path = self._artifact_path(monitor.workspace_id, monitor.id, run.id)
        temp_path = final_path.with_name(f".{final_path.name}.{report_id}.tmp")
        final_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with temp_path.open("wb") as stream:
                stream.write(rendered.content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_path, final_path)
            final_path.chmod(0o600)
        except Exception as exc:
            temp_path.unlink(missing_ok=True)
            raise ReportArtifactStorageError(f"情报报告无法安全保存：{exc}") from exc

        audit = result.get("audit") or {}
        artifact = IntelligenceReportArtifact(
            id=report_id,
            workspace_id=monitor.workspace_id,
            monitor_id=monitor.id,
            run_id=run.id,
            workflow=workflow,
            trigger=run.trigger,
            source_request_id=str(audit.get("request_id") or rendered.report_id or ""),
            filename=rendered.filename,
            storage_path=str(final_path),
            byte_size=len(rendered.content),
            sha256=sha256(rendered.content).hexdigest(),
            query_context=query_context,
            generated_at=self._utcnow(),
        )
        try:
            db.add(artifact)
            db.commit()
            db.refresh(artifact)
            return artifact
        except Exception:
            db.rollback()
            final_path.unlink(missing_ok=True)
            raise

    def latest_for_monitor(
        self,
        db: Session,
        monitor_id: str,
    ) -> Optional[IntelligenceReportArtifact]:
        return (
            db.query(IntelligenceReportArtifact)
            .filter(IntelligenceReportArtifact.monitor_id == monitor_id)
            .order_by(IntelligenceReportArtifact.generated_at.desc())
            .first()
        )

    def for_run(
        self,
        db: Session,
        run_id: str,
    ) -> Optional[IntelligenceReportArtifact]:
        return (
            db.query(IntelligenceReportArtifact)
            .filter(IntelligenceReportArtifact.run_id == run_id)
            .first()
        )

    def list_reports(
        self,
        db: Session,
        *,
        workspace_id: str,
        monitor_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[IntelligenceReportArtifact]:
        query = db.query(IntelligenceReportArtifact).filter(
            IntelligenceReportArtifact.workspace_id == workspace_id
        )
        if monitor_id:
            query = query.filter(IntelligenceReportArtifact.monitor_id == monitor_id)
        return query.order_by(IntelligenceReportArtifact.generated_at.desc()).limit(limit).all()

    def get_report(
        self,
        db: Session,
        report_id: str,
        *,
        workspace_id: str,
    ) -> IntelligenceReportArtifact:
        report = (
            db.query(IntelligenceReportArtifact)
            .filter(
                IntelligenceReportArtifact.id == report_id,
                IntelligenceReportArtifact.workspace_id == workspace_id,
            )
            .first()
        )
        if not report:
            raise ReportArtifactNotFoundError(report_id)
        return report

    def resolve_download_path(self, report: IntelligenceReportArtifact) -> Path:
        root = self.reports_dir.resolve()
        path = Path(report.storage_path).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ReportArtifactNotFoundError(report.id)
        if path.stat().st_size != report.byte_size:
            raise ReportArtifactStorageError("情报报告文件校验失败")
        digest = sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != report.sha256:
            raise ReportArtifactStorageError("情报报告文件完整性校验失败")
        return path

    def monitor_storage_paths(self, db: Session, monitor_id: str) -> List[str]:
        return [
            item.storage_path
            for item in (
                db.query(IntelligenceReportArtifact)
                .filter(IntelligenceReportArtifact.monitor_id == monitor_id)
                .all()
            )
        ]

    def delete_storage_paths(self, storage_paths: List[str]) -> None:
        root = self.reports_dir.resolve()
        for storage_path in storage_paths:
            try:
                path = Path(storage_path).resolve()
                if path.is_relative_to(root):
                    path.unlink(missing_ok=True)
            except OSError:
                continue


intelligence_report_artifact_service = IntelligenceReportArtifactService()
