"""Institutional Grok intelligence and multi-source research endpoints."""

from datetime import date
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.institutional_intelligence_service import institutional_intelligence_service
from app.services.intelligence_monitoring_service import (
    MonitorAlreadyRunningError,
    MonitorNotFoundError,
    SUPPORTED_INTERVAL_MINUTES,
    intelligence_monitoring_service,
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
        "items": [intelligence_monitoring_service.serialize_monitor(item) for item in monitors],
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
    return intelligence_monitoring_service.serialize_monitor(monitor)


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
    return intelligence_monitoring_service.serialize_monitor(monitor)


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
    return {"items": [intelligence_monitoring_service.serialize_run(item) for item in runs]}


@router.post("/realtime/search")
async def search_realtime_information(request: RealtimeResearchRequest):
    if request.date_from and request.date_to and request.date_from > request.date_to:
        raise HTTPException(status_code=422, detail="开始日期不能晚于结束日期")
    try:
        return await institutional_intelligence_service.search_realtime_information(
            request.model_dump()
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"实时信息检索失败：{exc}") from exc


@router.post("/project-risk/analyze")
async def analyze_project_risk(request: ProjectRiskRequest):
    try:
        return await institutional_intelligence_service.analyze_project_risk(request.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"项目风险情报生成失败：{exc}") from exc


@router.post("/geopolitical-impact/analyze")
async def analyze_geopolitical_impact(request: GeopoliticalImpactRequest):
    try:
        return await institutional_intelligence_service.analyze_geopolitical_impact(request.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"地缘融资推演失败：{exc}") from exc
