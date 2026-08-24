from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.services.model_governance_service import model_governance_service
from app.services.champion_challenger_service import champion_challenger_service
from app.services.audit_trail_service import audit_trail_service, AuditEventType
from app.services.emergency_shutdown_service import emergency_shutdown_service
from app.services.compliance_gate_service import compliance_gate_service
from app.services.role_permission_service import role_permission_service, Role, Permission

router = APIRouter(prefix="/api/v1/governance", tags=["governance"])


# Request/Response Models
class ApprovalRequest(BaseModel):
    notes: Optional[str] = None


class RejectionRequest(BaseModel):
    reason: str


class AliasRequest(BaseModel):
    alias: str
    model_id: str
    traffic_percentage: float = 0.0


class TrafficAllocationRequest(BaseModel):
    allocations: dict


class ShutdownRequest(BaseModel):
    reason: str
    description: str
    affected_systems: Optional[List[str]] = None


# Model Governance Endpoints
@router.get("/pending")
async def get_pending_approvals():
    """Get models pending approval."""
    try:
        models = await model_governance_service.get_pending_approvals()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve/{model_id}")
async def approve_model(model_id: str, request: ApprovalRequest):
    """Approve a model."""
    try:
        result = await model_governance_service.approve_model(
            model_id, approved_by="admin", notes=request.notes
        )

        # Log audit event
        await audit_trail_service.log_model_approval(
            model_id, "admin", "approve", request.notes
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reject/{model_id}")
async def reject_model(model_id: str, request: RejectionRequest):
    """Reject a model."""
    try:
        result = await model_governance_service.reject_model(
            model_id, rejected_by="admin", reason=request.reason
        )

        # Log audit event
        await audit_trail_service.log_model_approval(
            model_id, "admin", "reject", request.reason
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_governance_stats():
    """Get governance statistics."""
    try:
        stats = await model_governance_service.get_governance_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_approval_history(
    model_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    """Get approval history."""
    try:
        history = await model_governance_service.get_approval_history(
            model_id=model_id, limit=limit
        )
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Champion/Challenger Endpoints
@router.get("/aliases")
async def get_model_aliases():
    """Get all model aliases."""
    try:
        aliases = await champion_challenger_service.get_all_aliases()
        return {"aliases": aliases}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/aliases")
async def create_model_alias(request: AliasRequest):
    """Create or update a model alias."""
    try:
        result = await champion_challenger_service.create_alias(
            request.alias,
            request.model_id,
            traffic_percentage=request.traffic_percentage,
            created_by="admin",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aliases/{alias}/resolve")
async def resolve_alias(alias: str):
    """Resolve an alias to a model."""
    try:
        result = await champion_challenger_service.resolve_alias(alias)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/traffic")
async def get_traffic_allocation():
    """Get current traffic allocation."""
    try:
        allocation = await champion_challenger_service.get_traffic_allocation()
        return allocation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/traffic")
async def allocate_traffic(request: TrafficAllocationRequest):
    """Allocate traffic across aliases."""
    try:
        result = await champion_challenger_service.allocate_traffic(
            request.allocations, updated_by="admin"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Audit Trail Endpoints
@router.get("/audit/events")
async def get_audit_events(
    event_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """Get audit events."""
    try:
        event_type_enum = AuditEventType(event_type) if event_type else None
        events = await audit_trail_service.get_audit_events(
            event_type=event_type_enum,
            user_id=user_id,
            resource_type=resource_type,
            limit=limit,
        )
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/stats")
async def get_audit_stats():
    """Get audit trail statistics."""
    try:
        stats = await audit_trail_service.get_audit_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/export")
async def export_audit_trail(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """Export audit trail."""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        export = await audit_trail_service.export_audit_trail(
            start_date=start, end_date=end
        )
        return export
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Emergency Shutdown Endpoints
@router.get("/shutdown/status")
async def get_shutdown_status():
    """Get system shutdown status."""
    try:
        status = await emergency_shutdown_service.get_current_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shutdown/initiate")
async def initiate_shutdown(request: ShutdownRequest):
    """Initiate emergency shutdown."""
    try:
        from app.services.emergency_shutdown_service import ShutdownReason

        result = await emergency_shutdown_service.initiate_shutdown(
            reason=ShutdownReason.MANUAL,
            initiated_by="admin",
            description=request.description,
            affected_systems=request.affected_systems,
        )

        # Log audit event
        await audit_trail_service.log_event(
            event_type=AuditEventType.SYSTEM_EVENT,
            user_id="admin",
            action="emergency_shutdown",
            details={"reason": request.reason, "description": request.description},
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shutdown/recover")
async def initiate_recovery():
    """Initiate system recovery."""
    try:
        # Perform health checks
        health = await emergency_shutdown_service.check_system_health()

        recovery = await emergency_shutdown_service.initiate_recovery(
            initiated_by="admin",
            verification_checks=health.get("checks", {}),
        )
        result = await emergency_shutdown_service.complete_recovery(
            initiated_by="admin"
        )
        await audit_trail_service.log_event(
            event_type=AuditEventType.SYSTEM_EVENT,
            user_id="admin",
            action="emergency_recovery_completed",
            details={"health": health, "recovery": recovery},
        )
        return {**result, "health": health}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Compliance Endpoints
@router.post("/compliance/check")
async def check_compliance(data: dict):
    """Check compliance of data."""
    try:
        result = await compliance_gate_service.check_data_compliance(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Role/Permission Endpoints
@router.get("/roles")
async def get_roles():
    """Get all roles and permissions."""
    try:
        roles = role_permission_service.get_all_roles()
        return {"roles": roles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roles/{role}/permissions")
async def get_role_permissions(role: str):
    """Get permissions for a role."""
    try:
        role_enum = Role(role)
        permissions = role_permission_service.get_role_permissions(role_enum)
        return {"role": role, "permissions": permissions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
