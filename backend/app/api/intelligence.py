"""Institutional Grok intelligence and multi-source research endpoints."""

from datetime import date
from io import BytesIO
import json
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.institutional_intelligence_service import institutional_intelligence_service
from app.services.intelligence_pdf_service import intelligence_pdf_service
from app.services.intelligence_report_artifact_service import (
    ReportArtifactNotFoundError,
    ReportArtifactStorageError,
    intelligence_report_artifact_service,
)
from app.services.audit_trail_service import audit_trail_service, AuditEventType
from app.services.intelligence_monitoring_service import (
    MonitorAlreadyRunningError,
    MonitorNotFoundError,
    SUPPORTED_INTERVAL_MINUTES,
    intelligence_monitoring_service,
)
from app.services.intelligence_history_service import (
    HistoryRecordNotFoundError,
    SUPPORTED_HISTORY_WORKFLOWS,
    intelligence_history_service,
)


router = APIRouter(prefix="/api/v1/intelligence", tags=["institutional-intelligence"])


class ProjectRiskRequest(BaseModel):
    country: str = Field(min_length=2, max_length=120)
    project_name: str = Field(min_length=2, max_length=200)
    product_type: Literal[
        "sovereign_loan",
        "non_sovereign_finance",
        "guarantee",
        "co_financing",
        "equity",
    ] = "sovereign_loan"
    risk_focus: List[Literal["political", "social", "debt", "environment", "reputation"]] = Field(
        default_factory=lambda: ["political", "social", "debt", "environment", "reputation"]
    )
    window_days: int = Field(default=7, ge=1, le=90)
    monitoring_question: Optional[str] = Field(default=None, max_length=1000)
    workspace_id: str = Field(default="personal", min_length=1, max_length=80)


class GeopoliticalImpactRequest(BaseModel):
    issue: str = Field(min_length=4, max_length=1200)
    regions: List[str] = Field(default_factory=list, max_length=12)
    actors: List[str] = Field(default_factory=list, max_length=20)
    product_types: List[str] = Field(default_factory=list, max_length=10)
    horizon: Literal["quarter", "one_year", "three_years"] = "one_year"
    window_days: int = Field(default=30, ge=1, le=90)
    decision_question: Optional[str] = Field(default=None, max_length=1200)
    workspace_id: str = Field(default="personal", min_length=1, max_length=80)


class RealtimeResearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1600)
    keywords: List[str] = Field(default_factory=list, max_length=20)
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    source_channels: List[Literal["x", "web"]] = Field(
        default_factory=lambda: ["x", "web"], min_length=1, max_length=2
    )
    use_code_interpreter: bool = True
    preserve_x_original: bool = True
    max_results: int = Field(default=30, ge=1, le=50)
    workspace_id: str = Field(default="personal", min_length=1, max_length=80)


class IntelligenceMonitorCreate(BaseModel):
    monitor_type: Literal["realtime_research", "project_risk"]
    name: Optional[str] = Field(default=None, min_length=2, max_length=160)
    schedule_minutes: Literal[30, 60, 120, 240, 360, 480, 720, 1440] = 60
    request_payload: Dict[str, Any]
    workspace_id: str = Field(default="personal", min_length=1, max_length=80)
    is_active: bool = True


class IntelligenceMonitorUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=160)
    schedule_minutes: Optional[
        Literal[30, 60, 120, 240, 360, 480, 720, 1440]
    ] = None
    is_active: Optional[bool] = None


class IntelligencePdfExportRequest(BaseModel):
    workflow: Literal["realtime-research", "project-risk", "geopolitical-impact"]
    result: Dict[str, Any]
    query_context: Dict[str, Any] = Field(default_factory=dict)


HistoryWorkflow = Literal["realtime-research", "project-risk", "geopolitical-impact"]


def _validated_monitor_payload(
    monitor_type: str,
    payload: Dict[str, Any],
    workspace_id: str,
) -> Dict[str, Any]:
    scoped_payload = {**payload, "workspace_id": workspace_id}
    if monitor_type == "realtime_research":
        return RealtimeResearchRequest.model_validate(scoped_payload).model_dump(mode="json")
    return ProjectRiskRequest.model_validate(scoped_payload).model_dump(mode="json")


def _default_monitor_name(monitor_type: str, payload: Dict[str, Any]) -> str:
    if monitor_type == "realtime_research":
        return str(payload.get("query") or "实时信息监控")[:160]
    return f"{payload.get('country', '')} · {payload.get('project_name', '项目风险监控')}"[:160]


async def _save_analysis_history(
    db: Session,
    *,
    workflow: str,
    query_context: Dict[str, Any],
    result: Dict[str, Any],
):
    record = intelligence_history_service.save(
        db,
        workflow=workflow,
        query_context=query_context,
        result=result,
    )
    if not record:
        return result
    result["history_record"] = intelligence_history_service.serialize_summary(record)
    await audit_trail_service.log_event(
        event_type=AuditEventType.DATA_ACCESS,
        user_id=record.workspace_id,
        resource_type="intelligence_analysis_history",
        resource_id=record.id,
        action="save_analysis_history",
        details={
            "workflow": record.workflow,
            "trigger": record.trigger,
            "source_request_id": record.source_request_id,
        },
    )
    return result


@router.get("/capabilities")
async def get_intelligence_capabilities():
    capabilities = institutional_intelligence_service.capabilities()
    capabilities["monitoring"] = intelligence_monitoring_service.scheduler_status()
    return capabilities


@router.get("/monitors")
async def list_intelligence_monitors(
    workspace_id: str = "personal",
    monitor_type: Optional[Literal["realtime_research", "project_risk"]] = None,
    db: Session = Depends(get_db),
):
    monitors = intelligence_monitoring_service.list_monitors(
        db,
        workspace_id=workspace_id,
        monitor_type=monitor_type,
    )
    return {
        "items": [intelligence_monitoring_service.serialize_monitor(item, db) for item in monitors],
        "supported_interval_minutes": list(SUPPORTED_INTERVAL_MINUTES),
        "scheduler": intelligence_monitoring_service.scheduler_status(),
    }


@router.post("/monitors", status_code=201)
async def create_intelligence_monitor(
    request: IntelligenceMonitorCreate,
    db: Session = Depends(get_db),
):
    payload = _validated_monitor_payload(
        request.monitor_type,
        request.request_payload,
        request.workspace_id,
    )
    monitor = intelligence_monitoring_service.create_monitor(
        db,
        workspace_id=request.workspace_id,
        monitor_type=request.monitor_type,
        name=request.name or _default_monitor_name(request.monitor_type, payload),
        schedule_minutes=request.schedule_minutes,
        request_payload=payload,
        is_active=request.is_active,
    )
    return intelligence_monitoring_service.serialize_monitor(monitor, db)


@router.patch("/monitors/{monitor_id}")
async def update_intelligence_monitor(
    monitor_id: str,
    request: IntelligenceMonitorUpdate,
    db: Session = Depends(get_db),
):
    try:
        monitor = intelligence_monitoring_service.update_monitor(
            db,
            monitor_id,
            name=request.name,
            schedule_minutes=request.schedule_minutes,
            is_active=request.is_active,
        )
    except MonitorNotFoundError as exc:
        raise HTTPException(status_code=404, detail="监控任务不存在") from exc
    return intelligence_monitoring_service.serialize_monitor(monitor, db)


@router.delete("/monitors/{monitor_id}")
async def delete_intelligence_monitor(
    monitor_id: str,
    db: Session = Depends(get_db),
):
    try:
        intelligence_monitoring_service.delete_monitor(db, monitor_id)
    except MonitorNotFoundError as exc:
        raise HTTPException(status_code=404, detail="监控任务不存在") from exc
    return {"deleted": monitor_id}


@router.post("/monitors/{monitor_id}/run")
async def run_intelligence_monitor_now(monitor_id: str):
    try:
        return await intelligence_monitoring_service.execute_monitor(monitor_id, trigger="manual")
    except MonitorNotFoundError as exc:
        raise HTTPException(status_code=404, detail="监控任务不存在") from exc
    except MonitorAlreadyRunningError as exc:
        raise HTTPException(status_code=409, detail="该监控任务正在运行") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"监控任务执行失败：{exc}") from exc


@router.get("/monitors/{monitor_id}/runs")
async def list_intelligence_monitor_runs(
    monitor_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        runs = intelligence_monitoring_service.list_runs(db, monitor_id, limit=limit)
    except MonitorNotFoundError as exc:
        raise HTTPException(status_code=404, detail="监控任务不存在") from exc
    return {"items": [intelligence_monitoring_service.serialize_run(item, db) for item in runs]}


@router.get("/reports")
async def list_intelligence_reports(
    workspace_id: str = Query(default="personal", min_length=1, max_length=80),
    monitor_id: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    reports = intelligence_report_artifact_service.list_reports(
        db,
        workspace_id=workspace_id,
        monitor_id=monitor_id,
        limit=limit,
    )
    return {
        "items": [intelligence_report_artifact_service.serialize(item) for item in reports]
    }


@router.get("/reports/{report_id}/download")
async def download_intelligence_report(
    report_id: str,
    http_request: Request,
    workspace_id: str = Query(default="personal", min_length=1, max_length=80),
    db: Session = Depends(get_db),
):
    try:
        report = intelligence_report_artifact_service.get_report(
            db,
            report_id,
            workspace_id=workspace_id,
        )
        report_path = intelligence_report_artifact_service.resolve_download_path(report)
    except ReportArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail="定时情报报告不存在") from exc
    except ReportArtifactStorageError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    await audit_trail_service.log_event(
        event_type=AuditEventType.DATA_ACCESS,
        user_id=workspace_id,
        resource_type="intelligence_report",
        resource_id=report.id,
        action="download_monitor_pdf",
        details={
            "monitor_id": report.monitor_id,
            "run_id": report.run_id,
            "workflow": report.workflow,
            "source_request_id": report.source_request_id,
            "content_bytes": report.byte_size,
            "sha256": report.sha256,
        },
        ip_address=http_request.client.host if http_request.client else None,
        user_agent=http_request.headers.get("user-agent"),
    )
    encoded_filename = quote(report.filename)
    return FileResponse(
        report_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="intelligence-monitor-report.pdf"; '
                f"filename*=UTF-8''{encoded_filename}"
            ),
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Report-SHA256": report.sha256,
        },
    )


@router.get("/history")
async def list_intelligence_history(
    workspace_id: str = Query(default="personal", min_length=1, max_length=80),
    workflow: Optional[HistoryWorkflow] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    records = intelligence_history_service.list_records(
        db,
        workspace_id=workspace_id,
        workflow=workflow,
        limit=limit,
    )
    return {
        "items": [intelligence_history_service.serialize_summary(item) for item in records],
        "supported_workflows": list(SUPPORTED_HISTORY_WORKFLOWS),
    }


@router.get("/history/{record_id}/pdf")
async def export_intelligence_history_pdf(
    record_id: str,
    http_request: Request,
    workspace_id: str = Query(default="personal", min_length=1, max_length=80),
    db: Session = Depends(get_db),
):
    """Export the stored snapshot without calling Grok again."""
    try:
        record = intelligence_history_service.get_record(
            db,
            record_id,
            workspace_id=workspace_id,
        )
        report = intelligence_pdf_service.generate(
            record.workflow,
            record.result,
            record.query_context,
        )
    except HistoryRecordNotFoundError as exc:
        raise HTTPException(status_code=404, detail="历史分析记录不存在") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"历史记录 PDF 生成失败：{exc}") from exc

    await audit_trail_service.log_event(
        event_type=AuditEventType.DATA_ACCESS,
        user_id=workspace_id,
        resource_type="intelligence_analysis_history",
        resource_id=record.id,
        action="export_history_pdf",
        details={
            "workflow": record.workflow,
            "source_request_id": record.source_request_id,
            "content_bytes": len(report.content),
            "template_version": "1.0",
        },
        ip_address=http_request.client.host if http_request.client else None,
        user_agent=http_request.headers.get("user-agent"),
    )
    encoded_filename = quote(report.filename)
    return StreamingResponse(
        BytesIO(report.content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="intelligence-history-report.pdf"; '
                f"filename*=UTF-8''{encoded_filename}"
            ),
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Intelligence-History-Id": record.id,
        },
    )


@router.get("/history/{record_id}")
async def get_intelligence_history_record(
    record_id: str,
    workspace_id: str = Query(default="personal", min_length=1, max_length=80),
    db: Session = Depends(get_db),
):
    try:
        record = intelligence_history_service.get_record(
            db,
            record_id,
            workspace_id=workspace_id,
        )
    except HistoryRecordNotFoundError as exc:
        raise HTTPException(status_code=404, detail="历史分析记录不存在") from exc
    return intelligence_history_service.serialize_detail(record)


@router.post("/realtime/search")
async def search_realtime_information(
    request: RealtimeResearchRequest,
    db: Session = Depends(get_db),
):
    if request.date_from and request.date_to and request.date_from > request.date_to:
        raise HTTPException(status_code=422, detail="开始日期不能晚于结束日期")
    try:
        result = await institutional_intelligence_service.search_realtime_information(
            request.model_dump(mode="json")
        )
        return await _save_analysis_history(
            db,
            workflow="realtime-research",
            query_context=request.model_dump(mode="json"),
            result=result,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"实时信息检索失败：{exc}") from exc


@router.post("/project-risk/analyze")
async def analyze_project_risk(
    request: ProjectRiskRequest,
    db: Session = Depends(get_db),
):
    try:
        result = await institutional_intelligence_service.analyze_project_risk(
            request.model_dump(mode="json")
        )
        return await _save_analysis_history(
            db,
            workflow="project-risk",
            query_context=request.model_dump(mode="json"),
            result=result,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"项目风险情报生成失败：{exc}") from exc


@router.post("/geopolitical-impact/analyze")
async def analyze_geopolitical_impact(
    request: GeopoliticalImpactRequest,
    db: Session = Depends(get_db),
):
    try:
        result = await institutional_intelligence_service.analyze_geopolitical_impact(
            request.model_dump(mode="json")
        )
        return await _save_analysis_history(
            db,
            workflow="geopolitical-impact",
            query_context=request.model_dump(mode="json"),
            result=result,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"地缘融资推演失败：{exc}") from exc


@router.post("/export/pdf")
async def export_intelligence_pdf(
    export_request: IntelligencePdfExportRequest,
    http_request: Request,
):
    """Render a completed intelligence result without re-running the model."""
    serialized_size = len(
        json.dumps(export_request.model_dump(mode="json"), ensure_ascii=False).encode("utf-8")
    )
    if serialized_size > 2_000_000:
        raise HTTPException(status_code=413, detail="分析结果过大，无法安全导出 PDF")
    try:
        report = intelligence_pdf_service.generate(
            export_request.workflow,
            export_request.result,
            export_request.query_context,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF 生成失败：{exc}") from exc

    audit = export_request.result.get("audit") or {}
    await audit_trail_service.log_event(
        event_type=AuditEventType.DATA_ACCESS,
        user_id=str(audit.get("workspace_id") or "personal"),
        resource_type="intelligence_report",
        resource_id=report.report_id,
        action="export_pdf",
        details={
            "workflow": export_request.workflow,
            "source_request_id": audit.get("request_id"),
            "content_bytes": len(report.content),
            "template_version": "1.0",
        },
        ip_address=http_request.client.host if http_request.client else None,
        user_agent=http_request.headers.get("user-agent"),
    )
    encoded_filename = quote(report.filename)
    return StreamingResponse(
        BytesIO(report.content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="intelligence-report.pdf"; '
                f"filename*=UTF-8''{encoded_filename}"
            ),
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Intelligence-Request-Id": report.report_id,
        },
    )
