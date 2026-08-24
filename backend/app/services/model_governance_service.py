from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import logging

from app.models.training import Model, ModelStatus
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVOKED = "revoked"


class ApprovalAction(str, Enum):
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    REVOKE = "revoke"
    REQUEST_CHANGES = "request_changes"


class ModelGovernanceService:
    """Service for model governance and approval workflows."""

    async def submit_for_approval(
        self,
        model_id: str,
        submitted_by: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit a model for approval."""
        db = SessionLocal()
        try:
            model = db.query(Model).filter(Model.id == model_id).first()
            if not model:
                raise ValueError(f"Model {model_id} not found")

            if model.status not in [ModelStatus.TRAINED, ModelStatus.VALIDATED]:
                raise ValueError(f"Model must be trained/validated before submission")

            # Update model status
            model.status = ModelStatus.VALIDATED
            db.commit()

            # Create approval record
            approval = {
                "model_id": model_id,
                "action": ApprovalAction.SUBMIT.value,
                "performed_by": submitted_by,
                "notes": notes,
                "timestamp": datetime.utcnow().isoformat(),
            }

            return {
                "model_id": model_id,
                "status": "pending_approval",
                "submitted_by": submitted_by,
                "submitted_at": datetime.utcnow().isoformat(),
                "approval": approval,
            }

        finally:
            db.close()

    async def approve_model(
        self,
        model_id: str,
        approved_by: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Approve a model for deployment."""
        db = SessionLocal()
        try:
            model = db.query(Model).filter(Model.id == model_id).first()
            if not model:
                raise ValueError(f"Model {model_id} not found")

            if model.status != ModelStatus.VALIDATED:
                raise ValueError(f"Model must be validated before approval")

            # Update model status
            model.status = ModelStatus.APPROVED
            model.approved_by = approved_by
            model.approved_at = datetime.utcnow()
            db.commit()

            # Create approval record
            approval = {
                "model_id": model_id,
                "action": ApprovalAction.APPROVE.value,
                "performed_by": approved_by,
                "notes": notes,
                "timestamp": datetime.utcnow().isoformat(),
            }

            return {
                "model_id": model_id,
                "status": "approved",
                "approved_by": approved_by,
                "approved_at": model.approved_at.isoformat(),
                "approval": approval,
            }

        finally:
            db.close()

    async def reject_model(
        self,
        model_id: str,
        rejected_by: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Reject a model."""
        db = SessionLocal()
        try:
            model = db.query(Model).filter(Model.id == model_id).first()
            if not model:
                raise ValueError(f"Model {model_id} not found")

            # Update model status
            model.status = ModelStatus.REJECTED
            model.rejection_reason = reason
            db.commit()

            # Create approval record
            approval = {
                "model_id": model_id,
                "action": ApprovalAction.REJECT.value,
                "performed_by": rejected_by,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
            }

            return {
                "model_id": model_id,
                "status": "rejected",
                "rejected_by": rejected_by,
                "reason": reason,
                "approval": approval,
            }

        finally:
            db.close()

    async def revoke_approval(
        self,
        model_id: str,
        revoked_by: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Revoke approval for a model."""
        db = SessionLocal()
        try:
            model = db.query(Model).filter(Model.id == model_id).first()
            if not model:
                raise ValueError(f"Model {model_id} not found")

            if model.status != ModelStatus.APPROVED:
                raise ValueError(f"Only approved models can be revoked")

            # Update model status
            model.status = ModelStatus.REJECTED
            model.rejection_reason = f"Approval revoked: {reason}"
            db.commit()

            # Create approval record
            approval = {
                "model_id": model_id,
                "action": ApprovalAction.REVOKE.value,
                "performed_by": revoked_by,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
            }

            return {
                "model_id": model_id,
                "status": "revoked",
                "revoked_by": revoked_by,
                "reason": reason,
                "approval": approval,
            }

        finally:
            db.close()

    async def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all models pending approval."""
        db = SessionLocal()
        try:
            models = db.query(Model).filter(
                Model.status == ModelStatus.VALIDATED
            ).all()

            return [
                {
                    "model_id": m.id,
                    "name": m.name,
                    "model_type": m.model_type.value,
                    "version": m.version,
                    "status": m.status.value,
                    "created_by": m.created_by,
                    "created_at": m.created_at.isoformat(),
                    "metrics": {
                        "accuracy": m.accuracy,
                        "precision": m.precision,
                        "recall": m.recall,
                        "f1_score": m.f1_score,
                    },
                }
                for m in models
            ]

        finally:
            db.close()

    async def get_approval_history(
        self,
        model_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get approval history."""
        db = SessionLocal()
        try:
            query = db.query(Model)

            if model_id:
                query = query.filter(Model.id == model_id)

            # Get models with approval info
            models = query.filter(
                Model.approved_by.isnot(None) | Model.rejection_reason.isnot(None)
            ).order_by(Model.updated_at.desc()).limit(limit).all()

            history = []
            for m in models:
                if m.approved_by:
                    history.append({
                        "model_id": m.id,
                        "action": "approved",
                        "performed_by": m.approved_by,
                        "timestamp": m.approved_at.isoformat() if m.approved_at else None,
                    })
                if m.rejection_reason:
                    history.append({
                        "model_id": m.id,
                        "action": "rejected",
                        "reason": m.rejection_reason,
                        "timestamp": m.updated_at.isoformat(),
                    })

            return history

        finally:
            db.close()

    async def get_governance_stats(self) -> Dict[str, Any]:
        """Get governance statistics."""
        db = SessionLocal()
        try:
            total_models = db.query(Model).count()
            approved = db.query(Model).filter(Model.status == ModelStatus.APPROVED).count()
            rejected = db.query(Model).filter(Model.status == ModelStatus.REJECTED).count()
            pending = db.query(Model).filter(Model.status == ModelStatus.VALIDATED).count()
            deployed = db.query(Model).filter(Model.status == ModelStatus.DEPLOYED).count()

            return {
                "total_models": total_models,
                "approved": approved,
                "rejected": rejected,
                "pending_approval": pending,
                "deployed": deployed,
                "approval_rate": approved / (approved + rejected) if (approved + rejected) > 0 else 0,
            }

        finally:
            db.close()


# Global service instance
model_governance_service = ModelGovernanceService()
