from typing import Optional, Dict, Any, List
from datetime import datetime
import hashlib
import json
import logging

from app.models.training import Model, ModelStatus, ModelAlias, ModelDeployment
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class ModelVersionService:
    """Service for model version management with immutable versions."""

    async def create_version(
        self,
        model_id: str,
        version_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new immutable version of a model."""
        db = SessionLocal()
        try:
            model = db.query(Model).filter(Model.id == model_id).first()
            if not model:
                raise ValueError(f"Model {model_id} not found")

            if model.status != ModelStatus.TRAINED:
                raise ValueError(f"Model must be trained before creating a version")

            # Generate version hash
            version_hash = self._generate_version_hash(model)

            # Update model with version info
            model.version = version_hash
            model.status = ModelStatus.VALIDATED
            db.commit()

            return {
                "model_id": model_id,
                "version": version_hash,
                "version_notes": version_notes,
                "status": "validated",
                "created_at": datetime.utcnow().isoformat(),
            }

        finally:
            db.close()

    async def approve_version(
        self,
        model_id: str,
        approved_by: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Approve a model version for deployment."""
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

            return {
                "model_id": model_id,
                "version": model.version,
                "status": "approved",
                "approved_by": approved_by,
                "approved_at": model.approved_at.isoformat(),
            }

        finally:
            db.close()

    async def reject_version(
        self,
        model_id: str,
        rejected_by: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Reject a model version."""
        db = SessionLocal()
        try:
            model = db.query(Model).filter(Model.id == model_id).first()
            if not model:
                raise ValueError(f"Model {model_id} not found")

            # Update model status
            model.status = ModelStatus.REJECTED
            model.rejection_reason = reason
            db.commit()

            return {
                "model_id": model_id,
                "version": model.version,
                "status": "rejected",
                "rejected_by": rejected_by,
                "reason": reason,
            }

        finally:
            db.close()

    async def create_alias(
        self,
        alias: str,
        model_id: str,
        traffic_percentage: float = 0.0,
    ) -> Dict[str, Any]:
        """Create or update a model alias (champion/challenger)."""
        db = SessionLocal()
        try:
            # Check if model exists and is approved
            model = db.query(Model).filter(Model.id == model_id).first()
            if not model:
                raise ValueError(f"Model {model_id} not found")

            if model.status != ModelStatus.APPROVED:
                raise ValueError(f"Model must be approved before creating alias")

            # Check if alias exists
            existing_alias = db.query(ModelAlias).filter(ModelAlias.alias == alias).first()

            if existing_alias:
                # Update existing alias
                existing_alias.model_id = model_id
                existing_alias.traffic_percentage = traffic_percentage
                existing_alias.updated_at = datetime.utcnow()
            else:
                # Create new alias
                new_alias = ModelAlias(
                    alias=alias,
                    model_id=model_id,
                    traffic_percentage=traffic_percentage,
                )
                db.add(new_alias)

            db.commit()

            return {
                "alias": alias,
                "model_id": model_id,
                "version": model.version,
                "traffic_percentage": traffic_percentage,
                "created_at": datetime.utcnow().isoformat(),
            }

        finally:
            db.close()

    async def resolve_alias(
        self,
        alias: str,
    ) -> Dict[str, Any]:
        """Resolve an alias to a specific model version."""
        db = SessionLocal()
        try:
            alias_record = db.query(ModelAlias).filter(
                ModelAlias.alias == alias,
                ModelAlias.is_active == True,
            ).first()

            if not alias_record:
                raise ValueError(f"Alias '{alias}' not found or inactive")

            model = db.query(Model).filter(Model.id == alias_record.model_id).first()
            if not model:
                raise ValueError(f"Model for alias '{alias}' not found")

            return {
                "alias": alias,
                "model_id": model.id,
                "version": model.version,
                "model_type": model.model_type.value,
                "traffic_percentage": alias_record.traffic_percentage,
            }

        finally:
            db.close()

    async def deploy_model(
        self,
        model_id: str,
        environment: str,
        alias: Optional[str] = None,
        traffic_percentage: float = 100.0,
    ) -> Dict[str, Any]:
        """Deploy a model to an environment."""
        db = SessionLocal()
        try:
            model = db.query(Model).filter(Model.id == model_id).first()
            if not model:
                raise ValueError(f"Model {model_id} not found")

            if model.status != ModelStatus.APPROVED:
                raise ValueError(f"Model must be approved before deployment")

            # Create deployment record
            deployment = ModelDeployment(
                model_id=model_id,
                environment=environment,
                alias=alias,
                traffic_percentage=traffic_percentage,
                is_active=True,
                deployed_at=datetime.utcnow(),
            )
            db.add(deployment)

            # Update model status
            model.status = ModelStatus.DEPLOYED

            # Update alias if provided
            if alias:
                alias_record = db.query(ModelAlias).filter(ModelAlias.alias == alias).first()
                if alias_record:
                    alias_record.model_id = model_id
                    alias_record.traffic_percentage = traffic_percentage

            db.commit()

            return {
                "deployment_id": deployment.id,
                "model_id": model_id,
                "version": model.version,
                "environment": environment,
                "alias": alias,
                "traffic_percentage": traffic_percentage,
                "deployed_at": deployment.deployed_at.isoformat(),
            }

        finally:
            db.close()

    async def get_version_history(
        self,
        model_name: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get version history for models."""
        db = SessionLocal()
        try:
            query = db.query(Model).filter(Model.version.isnot(None))

            if model_name:
                query = query.filter(Model.name == model_name)

            models = query.order_by(Model.created_at.desc()).limit(limit).all()

            return [
                {
                    "model_id": m.id,
                    "name": m.name,
                    "version": m.version,
                    "model_type": m.model_type.value,
                    "status": m.status.value,
                    "created_at": m.created_at.isoformat(),
                    "approved_by": m.approved_by,
                    "approved_at": m.approved_at.isoformat() if m.approved_at else None,
                }
                for m in models
            ]

        finally:
            db.close()

    async def get_active_deployments(self) -> List[Dict[str, Any]]:
        """Get all active deployments."""
        db = SessionLocal()
        try:
            deployments = db.query(ModelDeployment).filter(
                ModelDeployment.is_active == True
            ).all()

            result = []
            for d in deployments:
                model = db.query(Model).filter(Model.id == d.model_id).first()
                result.append({
                    "deployment_id": d.id,
                    "model_id": d.model_id,
                    "model_name": model.name if model else None,
                    "version": model.version if model else None,
                    "environment": d.environment,
                    "alias": d.alias,
                    "traffic_percentage": d.traffic_percentage,
                    "deployed_at": d.deployed_at.isoformat(),
                    "requests_count": d.requests_count,
                })

            return result

        finally:
            db.close()

    def _generate_version_hash(self, model: Model) -> str:
        """Generate immutable version hash for a model."""
        # Create hash from model properties
        content = json.dumps({
            "model_id": model.id,
            "model_type": model.model_type.value,
            "hyperparameters": model.hyperparameters,
            "features": model.features,
            "training_samples": model.training_samples,
            "trained_at": model.trained_at.isoformat() if model.trained_at else None,
            "model_path": model.model_path,
        }, sort_keys=True)

        return hashlib.sha256(content.encode()).hexdigest()[:12]


# Global service instance
model_version_service = ModelVersionService()
