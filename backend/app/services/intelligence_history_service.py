"""Immutable, workspace-scoped history for decision-intelligence analyses."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.intelligence_monitoring import IntelligenceAnalysisRecord


SUPPORTED_HISTORY_WORKFLOWS = (
    "realtime-research",
    "project-risk",
    "geopolitical-impact",
)
EXPORTABLE_STATUSES = {"live", "partial"}
MAX_RECORD_BYTES = 2_000_000


class HistoryRecordNotFoundError(LookupError):
    pass


class HistoryRecordTooLargeError(ValueError):
    pass


class IntelligenceHistoryService:
    """Store the exact input and output used for a completed analysis."""

    @staticmethod
    def _iso(value) -> Optional[str]:
        if value is None:
            return None
        return value.isoformat(timespec="seconds") + "Z"

    @staticmethod
    def _clean_result(result: Dict[str, Any]) -> Dict[str, Any]:
        clean = deepcopy(result)
        clean.pop("history_record", None)
        return clean

    @staticmethod
    def _title(workflow: str, context: Dict[str, Any]) -> str:
        if workflow == "realtime-research":
            return str(context.get("query") or "实时信息检索")[:160]
        if workflow == "project-risk":
            country = str(context.get("country") or "未指定地区").strip()
            project = str(context.get("project_name") or "项目风险分析").strip()
            return f"{country} · {project}"[:160]
        return str(context.get("issue") or "地缘融资推演")[:160]

    def serialize_summary(self, record: IntelligenceAnalysisRecord) -> Dict[str, Any]:
        result = record.result or {}
        analysis = result.get("analysis") or {}
        summary = analysis.get("executive_summary") or analysis.get("direct_assessment") or ""
        return {
            "id": record.id,
            "workspace_id": record.workspace_id,
            "workflow": record.workflow,
            "title": record.title,
            "status": record.status,
            "trigger": record.trigger,
            "monitor_id": record.monitor_id,
            "run_id": record.run_id,
            "source_request_id": record.source_request_id,
            "source_count": len(result.get("evidence") or []),
            "summary": str(summary)[:300],
            "created_at": self._iso(record.created_at),
        }

    def serialize_detail(self, record: IntelligenceAnalysisRecord) -> Dict[str, Any]:
        return {
            **self.serialize_summary(record),
            "query_context": record.query_context or {},
            "result": record.result or {},
        }

    def save(
        self,
        db: Session,
        *,
        workflow: str,
        query_context: Dict[str, Any],
        result: Dict[str, Any],
        trigger: str = "manual",
        monitor_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Optional[IntelligenceAnalysisRecord]:
        if workflow not in SUPPORTED_HISTORY_WORKFLOWS:
            raise ValueError(f"Unsupported intelligence workflow: {workflow}")
        status = str(result.get("status") or "")
        if status not in EXPORTABLE_STATUSES or not result.get("analysis"):
            return None

        workspace_id = str(
            query_context.get("workspace_id")
            or (result.get("audit") or {}).get("workspace_id")
            or "personal"
        )
        source_request_id = str((result.get("audit") or {}).get("request_id") or "") or None
        existing = None
        if run_id:
            existing = (
                db.query(IntelligenceAnalysisRecord)
                .filter(IntelligenceAnalysisRecord.run_id == run_id)
                .first()
            )
        elif source_request_id:
            existing = (
                db.query(IntelligenceAnalysisRecord)
                .filter(
                    IntelligenceAnalysisRecord.workspace_id == workspace_id,
                    IntelligenceAnalysisRecord.workflow == workflow,
                    IntelligenceAnalysisRecord.source_request_id == source_request_id,
                )
                .first()
            )
        if existing:
            return existing

        clean_result = self._clean_result(result)
        serialized_size = len(
            json.dumps(
                {"query_context": query_context, "result": clean_result},
                ensure_ascii=False,
                default=str,
            ).encode("utf-8")
        )
        if serialized_size > MAX_RECORD_BYTES:
            raise HistoryRecordTooLargeError("分析结果超过历史记录安全上限")

        record = IntelligenceAnalysisRecord(
            workspace_id=workspace_id,
            workflow=workflow,
            title=self._title(workflow, query_context),
            status=status,
            trigger=trigger,
            monitor_id=monitor_id,
            run_id=run_id,
            source_request_id=source_request_id,
            query_context=deepcopy(query_context),
            result=clean_result,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def list_records(
        self,
        db: Session,
        *,
        workspace_id: str,
        workflow: Optional[str] = None,
        limit: int = 50,
    ) -> List[IntelligenceAnalysisRecord]:
        query = db.query(IntelligenceAnalysisRecord).filter(
            IntelligenceAnalysisRecord.workspace_id == workspace_id
        )
        if workflow:
            query = query.filter(IntelligenceAnalysisRecord.workflow == workflow)
        return query.order_by(IntelligenceAnalysisRecord.created_at.desc()).limit(limit).all()

    def get_record(
        self,
        db: Session,
        record_id: str,
        *,
        workspace_id: str,
    ) -> IntelligenceAnalysisRecord:
        record = (
            db.query(IntelligenceAnalysisRecord)
            .filter(
                IntelligenceAnalysisRecord.id == record_id,
                IntelligenceAnalysisRecord.workspace_id == workspace_id,
            )
            .first()
        )
        if not record:
            raise HistoryRecordNotFoundError(record_id)
        return record


intelligence_history_service = IntelligenceHistoryService()
