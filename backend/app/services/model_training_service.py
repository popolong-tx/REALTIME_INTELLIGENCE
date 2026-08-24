from typing import Optional, Dict, Any, List
from datetime import datetime
import numpy as np
import logging
import os
import joblib

from app.models.training import Model, ModelStatus, ModelType, TrainingRun
from app.core.database import SessionLocal
from app.models.platform_operations import utcnow_naive

logger = logging.getLogger(__name__)


class ModelTrainingService:
    """Service for training models."""

    def __init__(self):
        self.models_dir = "models"
        os.makedirs(self.models_dir, exist_ok=True)

    async def train_model(
        self,
        model_id: str,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        data_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Train a model."""
        db = SessionLocal()
        model = None
        try:
            # Get model
            model = db.query(Model).filter(Model.id == model_id).first()
            if not model:
                raise ValueError(f"Model {model_id} not found")

            # Update status
            model.status = ModelStatus.TRAINING
            db.commit()

            # Create training run
            training_run = TrainingRun(
                model_id=model_id,
                run_config={
                    "train_samples": len(X_train),
                    "val_samples": len(X_val) if X_val is not None else 0,
                    **(data_context or {}),
                },
                hyperparameters=model.hyperparameters,
                status="running",
                started_at=utcnow_naive(),
            )
            db.add(training_run)
            db.commit()

            # Get model instance
            model_instance = self._create_model_instance(
                model.model_type,
                model.hyperparameters,
            )

            # Train model
            start_time = utcnow_naive()
            model_instance.fit(X_train, y_train)
            training_time = (utcnow_naive() - start_time).total_seconds()

            # Calculate training metrics
            train_pred = model_instance.predict(X_train)
            train_metrics = self._calculate_metrics(y_train, train_pred)

            # Calculate validation metrics
            val_metrics = {}
            if X_val is not None and y_val is not None:
                val_pred = model_instance.predict(X_val)
                val_metrics = self._calculate_metrics(y_val, val_pred)

            # Update model
            model.status = ModelStatus.TRAINED
            model.trained_at = utcnow_naive()
            model.training_samples = len(X_train)
            if data_context:
                model.features = data_context.get("features")
                model.target_variable = data_context.get("target_column")

            # Update metrics
            model.accuracy = val_metrics.get(
                "direction_accuracy", train_metrics.get("direction_accuracy")
            )
            model.precision = val_metrics.get("precision", train_metrics.get("precision"))
            model.recall = val_metrics.get("recall", train_metrics.get("recall"))
            model.f1_score = val_metrics.get("f1_score", train_metrics.get("f1_score"))

            # Save model artifact
            # Safety: joblib used for local ML model serialization only.
            # Models are created internally from trusted sklearn/xgb libraries, not from untrusted sources.
            model_path = os.path.join(self.models_dir, f"{model_id}.joblib")
            joblib.dump(model_instance, model_path)
            model.model_path = model_path
            model.model_size_bytes = os.path.getsize(model_path)

            # Update training run
            training_run.status = "completed"
            training_run.completed_at = utcnow_naive()
            training_run.training_time_seconds = training_time
            training_run.training_loss = train_metrics.get("mse")
            training_run.validation_loss = val_metrics.get("mse")
            training_run.validation_metrics = {
                "train": train_metrics,
                "val": val_metrics,
            }

            db.commit()

            return {
                "model_id": model_id,
                "status": "trained",
                "training_time": training_time,
                "train_metrics": train_metrics,
                "val_metrics": val_metrics,
                "model_path": model_path,
            }

        except Exception as e:
            logger.error(f"Error training model {model_id}: {e}")
            if model:
                model.status = ModelStatus.DRAFT
                db.commit()
            raise
        finally:
            db.close()

    async def train_ensemble(
        self,
        model_ids: List[str],
        X_train: np.ndarray,
        y_train: np.ndarray,
        weights: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Train an ensemble of models."""
        db = SessionLocal()
        try:
            models = []
            for model_id in model_ids:
                model = db.query(Model).filter(Model.id == model_id).first()
                if not model or not model.model_path:
                    raise ValueError(f"Model {model_id} not found or not trained")
                # Safety: Loading locally-created model artifacts only.
                # These are internal models, not from untrusted external sources.
                model_instance = joblib.load(model.model_path)
                models.append(model_instance)

            # Create ensemble predictions
            if weights is None:
                weights = [1.0 / len(models)] * len(models)

            # Train each model on the data
            for model_instance in models:
                model_instance.fit(X_train, y_train)

            return {
                "model_ids": model_ids,
                "weights": weights,
                "model_count": len(models),
                "status": "trained",
            }

        except Exception as e:
            logger.error(f"Error training ensemble: {e}")
            raise
        finally:
            db.close()

    def _create_model_instance(
        self,
        model_type: str,
        hyperparameters: Optional[Dict] = None,
    ):
        """Create model instance based on type."""
        from sklearn.linear_model import LinearRegression, LogisticRegression
        from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
        from sklearn.svm import SVR, SVC

        params = hyperparameters or {}

        if model_type == ModelType.LINEAR_REGRESSION:
            return LinearRegression(**params)
        elif model_type == ModelType.RANDOM_FOREST:
            return RandomForestRegressor(**params)
        elif model_type == ModelType.XGBOOST:
            try:
                import xgboost as xgb
            except ImportError as exc:
                raise ValueError(
                    "XGBoost model type requires the optional xgboost dependency"
                ) from exc
            return xgb.XGBRegressor(**params)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

    def _calculate_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> Dict[str, float]:
        """Calculate regression metrics."""
        from sklearn.metrics import (
            mean_squared_error,
            mean_absolute_error,
            r2_score,
        )

        mse = mean_squared_error(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        rmse = np.sqrt(mse)

        # Direction accuracy
        direction_true = (y_true > 0).astype(int)
        direction_pred = (y_pred > 0).astype(int)
        direction_accuracy = np.mean(direction_true == direction_pred)

        return {
            "mse": float(mse),
            "rmse": float(rmse),
            "mae": float(mae),
            "r2": float(r2),
            "direction_accuracy": float(direction_accuracy),
        }

    def predict(
        self,
        model_id: str,
        X: np.ndarray,
    ) -> np.ndarray:
        """Make predictions using a trained model."""
        db = SessionLocal()
        try:
            model = db.query(Model).filter(Model.id == model_id).first()
            if not model or not model.model_path:
                raise ValueError(f"Model {model_id} not found or not trained")

            # Safety: Loading locally-created model artifact only
            model_instance = joblib.load(model.model_path)
            return model_instance.predict(X)

        finally:
            db.close()


# Global service instance
model_training_service = ModelTrainingService()
