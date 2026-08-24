from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.services.recommendation_engine import recommendation_engine
from app.services.single_stock_recommendation import single_stock_recommendation_service
from app.services.portfolio_recommendation import portfolio_recommendation_service
from app.services.phased_plan_generator import phased_plan_generator
from app.services.recommendation_history_service import recommendation_history_service
from app.services.recommendation_expiration_service import recommendation_expiration_service
from app.services.compliance_gate_service import compliance_gate_service
from app.services.prohibited_language_service import prohibited_language_service
from app.services.emergency_shutdown_service import emergency_shutdown_service
from app.services.trading_plan_service import (
    trading_plan_service,
    TradingPlanNotFoundError,
)
from app.services.audit_trail_service import audit_trail_service, AuditEventType

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


# Request/Response Models
class GenerateRecommendationRequest(BaseModel):
    symbol: str
    user_profile: Optional[dict] = None
    include_analysis: bool = True


class GeneratePlanRequest(BaseModel):
    symbol: str
    user_profile: dict
    workspace_id: str = "personal"
    plan_context: Optional[dict] = None
    evidence_status: str = "partial"


class PortfolioRequest(BaseModel):
    symbols: List[str]
    user_profile: Optional[dict] = None
    current_portfolio: Optional[dict] = None


class PlanStatusRequest(BaseModel):
    status: str
    workspace_id: str = "personal"


class ImportPlanRequest(BaseModel):
    workspace_id: str = "personal"
    symbol: str
    evidence_status: str = "partial"
    user_plan: dict
    generated_plan: dict


async def ensure_recommendations_operational() -> None:
    if not await emergency_shutdown_service.is_operation_allowed("recommendations"):
        raise HTTPException(
            status_code=503,
            detail={
                "code": "emergency_shutdown",
                "message": "Recommendation generation is blocked by the emergency shutdown gate.",
            },
        )


# Endpoints
@router.get("/")
async def list_recommendations(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    limit: int = Query(50, ge=1, le=100),
):
    """List recommendations."""
    try:
        history = await recommendation_history_service.get_recommendation_history(
            symbol=symbol, limit=limit
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_recommendation(request: GenerateRecommendationRequest):
    """Generate a trading recommendation."""
    await ensure_recommendations_operational()
    try:
        # Generate recommendation
        recommendation = await single_stock_recommendation_service.get_recommendation(
            request.symbol,
            user_profile=request.user_profile,
            include_analysis=request.include_analysis,
        )

        # Check compliance
        compliance = await compliance_gate_service.check_recommendation_compliance(
            recommendation
        )

        if not compliance["passed"]:
            return {
                "warning": "Recommendation may not meet compliance requirements",
                "compliance_issues": compliance["issues"],
                "recommendation": recommendation,
            }

        # Save to history
        await recommendation_history_service.save_recommendation(
            symbol=request.symbol,
            recommendation=recommendation.get("recommendation"),
            confidence=recommendation.get("confidence"),
            risk_level=recommendation.get("risk_level"),
            entry_price=recommendation.get("entry_price"),
            target_price=recommendation.get("target_price"),
            stop_loss=recommendation.get("stop_loss"),
        )

        await audit_trail_service.log_event(
            event_type=AuditEventType.RECOMMENDATION_GENERATED,
            user_id="api_user",
            resource_type="recommendation",
            action="generate_recommendation",
            details={"symbol": request.symbol},
        )

        return {"recommendation": recommendation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-plan")
async def generate_trading_plan(request: GeneratePlanRequest):
    """Generate a phased trading plan."""
    await ensure_recommendations_operational()
    try:
        plan = await phased_plan_generator.generate_plan(
            request.symbol,
            user_profile=request.user_profile,
        )

        record = trading_plan_service.create_plan(
            workspace_id=request.workspace_id,
            symbol=request.symbol,
            evidence_status=request.evidence_status,
            user_plan=request.plan_context or {
                "symbol": request.symbol,
                **request.user_profile,
            },
            generated_plan=plan,
        )
        await audit_trail_service.log_event(
            event_type=AuditEventType.RECOMMENDATION_GENERATED,
            user_id="api_user",
            resource_type="trading_plan",
            resource_id=record["id"],
            action="generate_plan",
            details={
                "symbol": request.symbol,
                "workspace_id": request.workspace_id,
                "version": record["version"],
            },
        )
        return {"plan": plan, "record": record}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio")
async def get_portfolio_recommendation(request: PortfolioRequest):
    """Get portfolio recommendation."""
    await ensure_recommendations_operational()
    try:
        recommendation = await portfolio_recommendation_service.get_portfolio_recommendation(
            request.symbols,
            user_profile=request.user_profile,
            current_portfolio=request.current_portfolio,
        )

        return recommendation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans")
async def list_saved_plans(workspace_id: str = Query("personal")):
    """List plans from durable workspace storage."""
    return {
        "plans": trading_plan_service.list_plans(workspace_id),
        "storage": "database",
    }


@router.post("/plans/import")
async def import_saved_plan(request: ImportPlanRequest):
    """One-time migration path for plans created by the former browser store."""
    await ensure_recommendations_operational()
    record = trading_plan_service.create_plan(
        workspace_id=request.workspace_id,
        symbol=request.symbol,
        evidence_status=request.evidence_status,
        user_plan=request.user_plan,
        generated_plan=request.generated_plan,
    )
    await audit_trail_service.log_event(
        event_type=AuditEventType.CONFIG_CHANGE,
        user_id="api_user",
        resource_type="trading_plan",
        resource_id=record["id"],
        action="migrate_browser_plan",
        details={"workspace_id": request.workspace_id, "symbol": request.symbol},
    )
    return {"plan": record}


@router.patch("/plans/{plan_id}/status")
async def update_saved_plan_status(plan_id: str, request: PlanStatusRequest):
    """Freeze, resume, or otherwise update a saved simulated plan."""
    await ensure_recommendations_operational()
    try:
        plan = trading_plan_service.update_status(
            plan_id,
            request.status,
            workspace_id=request.workspace_id,
        )
        await audit_trail_service.log_event(
            event_type=AuditEventType.CONFIG_CHANGE,
            user_id="api_user",
            resource_type="trading_plan",
            resource_id=plan_id,
            action="update_plan_status",
            details={"status": request.status, "workspace_id": request.workspace_id},
        )
        return {"plan": plan}
    except TradingPlanNotFoundError:
        raise HTTPException(status_code=404, detail="Plan not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/quick/{symbol}")
async def get_quick_recommendation(symbol: str):
    """Get quick recommendation for a stock."""
    await ensure_recommendations_operational()
    try:
        recommendation = await single_stock_recommendation_service.get_quick_recommendation(
            symbol
        )
        return recommendation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare")
async def compare_recommendations(
    symbols: str = Query(..., description="Comma-separated symbols"),
):
    """Compare recommendations for multiple stocks."""
    await ensure_recommendations_operational()
    try:
        symbol_list = [s.strip() for s in symbols.split(",")]
        comparison = await single_stock_recommendation_service.compare_recommendations(
            symbol_list
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_recommendation_history(
    symbol: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    """Get recommendation history."""
    try:
        history = await recommendation_history_service.get_recommendation_history(
            symbol=symbol, limit=limit
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_recommendation_stats(
    symbol: Optional[str] = Query(None),
    days: int = Query(90, ge=1, le=365),
):
    """Get recommendation performance statistics."""
    try:
        stats = await recommendation_history_service.get_performance_stats(
            symbol=symbol, days=days
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_recommendations():
    """Get active recommendations."""
    try:
        active = await recommendation_expiration_service.get_active_recommendations()
        return {"recommendations": active}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expiring")
async def get_expiring_recommendations(
    days: int = Query(7, ge=1, le=30),
):
    """Get recommendations expiring soon."""
    try:
        expiring = await recommendation_expiration_service.get_expiring_recommendations(
            days=days
        )
        return {"recommendations": expiring}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{recommendation_id}/invalidate")
async def invalidate_recommendation(
    recommendation_id: str,
    reason: str = "",
):
    """Invalidate a recommendation."""
    try:
        result = await recommendation_expiration_service.invalidate_recommendation(
            recommendation_id, reason=reason
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-compliance")
async def check_compliance(recommendation: dict):
    """Check recommendation compliance."""
    try:
        compliance = await compliance_gate_service.check_recommendation_compliance(
            recommendation
        )

        # Check prohibited language
        language_check = prohibited_language_service.check_recommendation(recommendation)

        return {
            "compliance": compliance,
            "language_check": language_check,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
