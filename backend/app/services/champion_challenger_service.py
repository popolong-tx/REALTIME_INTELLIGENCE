from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.models.training import Model, ModelAlias, ModelDeployment, ModelStatus
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class ChampionChallengerService:
    """Service for managing champion/challenger model aliases."""

    async def create_alias(
        self,
        alias: str,
        model_id: str,
        traffic_percentage: float = 0.0,
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create or update a model alias."""
        db = SessionLocal()
        try:
            # Validate model exists and is approved
            model = db.query(Model).filter(Model.id == model_id).first()
            if not model:
                raise ValueError(f"Model {model_id} not found")

            if model.status not in [ModelStatus.APPROVED, ModelStatus.DEPLOYED]:
                raise ValueError(f"Model must be approved before creating alias")

            # Check if alias exists
            existing = db.query(ModelAlias).filter(ModelAlias.alias == alias).first()

            if existing:
                # Update existing alias
                existing.model_id = model_id
                existing.traffic_percentage = traffic_percentage
                existing.updated_at = datetime.utcnow()
                action = "updated"
            else:
                # Create new alias
                new_alias = ModelAlias(
                    alias=alias,
                    model_id=model_id,
                    traffic_percentage=traffic_percentage,
                )
                db.add(new_alias)
                action = "created"

            db.commit()

            return {
                "alias": alias,
                "model_id": model_id,
                "model_name": model.name,
                "model_version": model.version,
                "traffic_percentage": traffic_percentage,
                "action": action,
                "created_by": created_by,
                "timestamp": datetime.utcnow().isoformat(),
            }

        finally:
            db.close()

    async def resolve_alias(
        self,
        alias: str,
    ) -> Dict[str, Any]:
        """Resolve an alias to a specific model."""
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
                "model_name": model.name,
                "model_version": model.version,
                "model_type": model.model_type.value,
                "model_path": model.model_path,
                "traffic_percentage": alias_record.traffic_percentage,
                "is_active": alias_record.is_active,
            }

        finally:
            db.close()

    async def get_all_aliases(self) -> List[Dict[str, Any]]:
        """Get all model aliases."""
        db = SessionLocal()
        try:
            aliases = db.query(ModelAlias).filter(
                ModelAlias.is_active == True
            ).all()

            result = []
            for alias in aliases:
                model = db.query(Model).filter(Model.id == alias.model_id).first()
                result.append({
                    "alias": alias.alias,
                    "model_id": alias.model_id,
                    "model_name": model.name if model else None,
                    "model_version": model.version if model else None,
                    "traffic_percentage": alias.traffic_percentage,
                    "created_at": alias.created_at.isoformat(),
                    "updated_at": alias.updated_at.isoformat(),
                })

            return result

        finally:
            db.close()

    async def deactivate_alias(
        self,
        alias: str,
        deactivated_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Deactivate a model alias."""
        db = SessionLocal()
        try:
            alias_record = db.query(ModelAlias).filter(ModelAlias.alias == alias).first()
            if not alias_record:
                raise ValueError(f"Alias '{alias}' not found")

            alias_record.is_active = False
            alias_record.updated_at = datetime.utcnow()
            db.commit()

            return {
                "alias": alias,
                "is_active": False,
                "deactivated_by": deactivated_by,
                "timestamp": datetime.utcnow().isoformat(),
            }

        finally:
            db.close()

    async def allocate_traffic(
        self,
        allocations: Dict[str, float],
        updated_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Allocate traffic across multiple aliases."""
        db = SessionLocal()
        try:
            # Validate allocations sum to 100%
            total = sum(allocations.values())
            if abs(total - 100) > 0.01:
                raise ValueError(f"Allocations must sum to 100%, got {total}%")

            results = []
            for alias, percentage in allocations.items():
                alias_record = db.query(ModelAlias).filter(
                    ModelAlias.alias == alias,
                    ModelAlias.is_active == True,
                ).first()

                if not alias_record:
                    raise ValueError(f"Alias '{alias}' not found or inactive")

                alias_record.traffic_percentage = percentage
                alias_record.updated_at = datetime.utcnow()

                model = db.query(Model).filter(Model.id == alias_record.model_id).first()
                results.append({
                    "alias": alias,
                    "model_id": alias_record.model_id,
                    "model_name": model.name if model else None,
                    "traffic_percentage": percentage,
                })

            db.commit()

            return {
                "allocations": results,
                "total_traffic": total,
                "updated_by": updated_by,
                "timestamp": datetime.utcnow().isoformat(),
            }

        finally:
            db.close()

    async def swap_champion(
        self,
        new_champion_alias: str,
        old_champion_alias: str = "champion",
        swapped_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Swap champion model."""
        db = SessionLocal()
        try:
            # Get new champion
            new_champion = db.query(ModelAlias).filter(
                ModelAlias.alias == new_champion_alias,
                ModelAlias.is_active == True,
            ).first()

            if not new_champion:
                raise ValueError(f"Alias '{new_champion_alias}' not found")

            # Get old champion
            old_champion = db.query(ModelAlias).filter(
                ModelAlias.alias == old_champion_alias,
                ModelAlias.is_active == True,
            ).first()

            # Update old champion to challenger
            if old_champion:
                old_champion.alias = f"challenger_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                old_champion.traffic_percentage = 0
                old_champion.updated_at = datetime.utcnow()

            # Update new champion
            new_champion.alias = old_champion_alias
            new_champion.traffic_percentage = 100
            new_champion.updated_at = datetime.utcnow()

            db.commit()

            return {
                "old_champion": {
                    "alias": old_champion.alias if old_champion else None,
                    "model_id": old_champion.model_id if old_champion else None,
                },
                "new_champion": {
                    "alias": old_champion_alias,
                    "model_id": new_champion.model_id,
                },
                "swapped_by": swapped_by,
                "timestamp": datetime.utcnow().isoformat(),
            }

        finally:
            db.close()

    async def get_traffic_allocation(self) -> Dict[str, Any]:
        """Get current traffic allocation."""
        db = SessionLocal()
        try:
            aliases = db.query(ModelAlias).filter(
                ModelAlias.is_active == True,
                ModelAlias.traffic_percentage > 0,
            ).all()

            allocations = []
            for alias in aliases:
                model = db.query(Model).filter(Model.id == alias.model_id).first()
                allocations.append({
                    "alias": alias.alias,
                    "model_id": alias.model_id,
                    "model_name": model.name if model else None,
                    "model_version": model.version if model else None,
                    "traffic_percentage": alias.traffic_percentage,
                })

            return {
                "allocations": allocations,
                "total_traffic": sum(a["traffic_percentage"] for a in allocations),
                "timestamp": datetime.utcnow().isoformat(),
            }

        finally:
            db.close()


# Global service instance
champion_challenger_service = ChampionChallengerService()
