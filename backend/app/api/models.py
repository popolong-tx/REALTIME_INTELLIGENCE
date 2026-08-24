from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.training import Model, ModelStatus, ModelType
from app.services.model_training_service import model_training_service
from app.services.model_fine_tuning_service import model_fine_tuning_service
from app.services.model_evaluation_service import model_evaluation_service
from app.services.model_version_service import model_version_service
from app.services.model_governance_service import model_governance_service
from app.services.emergency_shutdown_service import emergency_shutdown_service
from app.services.audit_trail_service import audit_trail_service, AuditEventType

router = APIRouter(prefix="/api/v1/models", tags=["models"])


# Request/Response Models
class ModelCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    model_type: str
    hyperparameters: Optional[dict] = None


class ModelResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    model_type: str
    version: str
    status: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    created_at: str
    updated_at: str


class TrainingRequest(BaseModel):
    symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    target_column: str = "close"
    prediction_horizon: int = 5


class FineTuningRequest(BaseModel):
    symbol: str = "AAPL"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    target_column: str = "close"
    prediction_horizon: int = 5
    param_grid: Optional[dict] = None
    search_method: str = "grid"
    n_iter: int = 20
    cv: int = 5


class EvaluationRequest(BaseModel):
    symbol: str = "AAPL"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    target_column: str = "close"
    prediction_horizon: int = 5


async def ensure_models_operational() -> None:
    if not await emergency_shutdown_service.is_operation_allowed("models"):
        raise HTTPException(
            status_code=503,
            detail={
                "code": "emergency_shutdown",
                "message": "Model mutations are blocked by the emergency shutdown gate.",
            },
        )


# Endpoints
@router.get("/", response_model=List[ModelResponse])
async def list_models(
    status: Optional[str] = Query(None, description="Filter by status"),
    model_type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(50, ge=1, le=100),
):
    """List all models."""
    db = next(get_db())
    try:
        query = db.query(Model)

        if status:
            query = query.filter(Model.status == status)
        if model_type:
            query = query.filter(Model.model_type == model_type)

        models = query.order_by(Model.created_at.desc()).limit(limit).all()

        return [
            ModelResponse(
                id=m.id,
                name=m.name,
                description=m.description,
                model_type=m.model_type.value,
                version=m.version or "1.0",
                status=m.status.value,
                accuracy=m.accuracy,
                precision=m.precision,
                recall=m.recall,
                f1_score=m.f1_score,
                created_at=m.created_at.isoformat(),
                updated_at=m.updated_at.isoformat(),
            )
            for m in models
        ]
    finally:
        db.close()


@router.post("/", response_model=ModelResponse)
async def create_model(request: ModelCreateRequest):
    """Create a new model."""
    await ensure_models_operational()
    db = next(get_db())
    try:
        import uuid
        model = Model(
            id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            model_type=ModelType(request.model_type),
            hyperparameters=request.hyperparameters,
            version="1.0.0",
            status=ModelStatus.DRAFT,
            created_by="api_user",
        )
        db.add(model)
        db.commit()
        db.refresh(model)

        return ModelResponse(
            id=model.id,
            name=model.name,
            description=model.description,
            model_type=model.model_type.value,
            version=model.version,
            status=model.status.value,
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat(),
        )
    finally:
        db.close()


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: str):
    """Get model details."""
    db = next(get_db())
    try:
        model = db.query(Model).filter(Model.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        return ModelResponse(
            id=model.id,
            name=model.name,
            description=model.description,
            model_type=model.model_type.value,
            version=model.version or "1.0",
            status=model.status.value,
            accuracy=model.accuracy,
            precision=model.precision,
            recall=model.recall,
            f1_score=model.f1_score,
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat(),
        )
    finally:
        db.close()


@router.post("/{model_id}/train")
async def train_model(model_id: str, request: TrainingRequest):
    """Train a model."""
    await ensure_models_operational()
    try:
        # Prepare training data
        from app.services.training_data_service import training_data_service

        data = await training_data_service.prepare_training_data(
            request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            target_column=request.target_column,
            prediction_horizon=request.prediction_horizon,
        )

        # Train model
        import numpy as np
        X_train = np.array(data["data"]["X_train"])
        y_train = np.array(data["data"]["y_train"])
        X_val = np.array(data["data"]["X_val"])
        y_val = np.array(data["data"]["y_val"])

        result = await model_training_service.train_model(
            model_id,
            X_train,
            y_train,
            X_val,
            y_val,
            data_context={
                "symbol": request.symbol,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "target_column": request.target_column,
                "prediction_horizon": request.prediction_horizon,
                "features": data.get("features", []),
            },
        )

        await audit_trail_service.log_model_training(
            model_id,
            "api_user",
            {"operation": "train", "symbol": request.symbol, "result": result},
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/fine-tune")
async def fine_tune_model(model_id: str, request: FineTuningRequest):
    """Fine-tune model hyperparameters."""
    await ensure_models_operational()
    try:
        from app.services.training_data_service import training_data_service
        import numpy as np

        data = await training_data_service.prepare_training_data(
            request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            target_column=request.target_column,
            prediction_horizon=request.prediction_horizon,
        )
        X_train = np.array(data["data"]["X_train"])
        y_train = np.array(data["data"]["y_train"])
        result = await model_fine_tuning_service.fine_tune_model(
            model_id,
            X_train,
            y_train,
            param_grid=request.param_grid,
            search_method=request.search_method,
            n_iter=request.n_iter,
            cv=request.cv,
            data_context={
                "symbol": request.symbol,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "target_column": request.target_column,
                "prediction_horizon": request.prediction_horizon,
                "features": data.get("features", []),
            },
        )
        await audit_trail_service.log_model_training(
            model_id,
            "api_user",
            {"operation": "fine_tune", "symbol": request.symbol, "result": result},
        )
        return {"status": "fine_tuned", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/evaluate")
async def evaluate_model(model_id: str, request: Optional[EvaluationRequest] = None):
    """Evaluate model performance."""
    await ensure_models_operational()
    try:
        from app.services.training_data_service import training_data_service
        import numpy as np

        evaluation = request or EvaluationRequest()
        data = await training_data_service.prepare_training_data(
            evaluation.symbol,
            start_date=evaluation.start_date,
            end_date=evaluation.end_date,
            target_column=evaluation.target_column,
            prediction_horizon=evaluation.prediction_horizon,
        )
        X_test = np.array(data["data"]["X_test"])
        y_test = np.array(data["data"]["y_test"])
        result = await model_evaluation_service.evaluate_model(model_id, X_test, y_test)
        await audit_trail_service.log_event(
            event_type=AuditEventType.MODEL_TRAINING,
            user_id="api_user",
            resource_type="model",
            resource_id=model_id,
            action="evaluate_model",
            details={"symbol": evaluation.symbol, "sample_count": result["sample_count"]},
        )
        return {
            "status": "evaluated",
            "data_source": {
                "symbol": evaluation.symbol,
                "features": data.get("features", []),
                "prepared_at": data.get("prepared_at"),
            },
            **result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/approve")
async def approve_model(model_id: str):
    """Approve a model for deployment."""
    await ensure_models_operational()
    try:
        result = await model_governance_service.approve_model(
            model_id, approved_by="api_user"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/reject")
async def reject_model(model_id: str, reason: str = ""):
    """Reject a model."""
    await ensure_models_operational()
    try:
        result = await model_governance_service.reject_model(
            model_id, rejected_by="api_user", reason=reason
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{model_id}/deploy")
async def deploy_model(
    model_id: str,
    environment: str = "production",
    alias: Optional[str] = None,
):
    """Deploy a model."""
    await ensure_models_operational()
    try:
        result = await model_version_service.deploy_model(
            model_id, environment=environment, alias=alias
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}/versions")
async def get_model_versions(model_id: str):
    """Get model version history."""
    try:
        versions = await model_version_service.get_version_history(model_id)
        return {"model_id": model_id, "versions": versions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
