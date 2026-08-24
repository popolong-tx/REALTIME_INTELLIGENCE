from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import numpy as np
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
import joblib
import os

from app.models.training import Model, ModelStatus, TrainingRun
from app.core.database import SessionLocal
from app.models.platform_operations import utcnow_naive

logger = logging.getLogger(__name__)


class ModelFineTuningService:
    """Service for model fine-tuning and hyperparameter optimization."""

    def __init__(self):
        self.models_dir = "models"
        os.makedirs(self.models_dir, exist_ok=True)

    async def fine_tune_model(
        self,
        model_id: str,
        X_train: np.ndarray,
        y_train: np.ndarray,
        param_grid: Optional[Dict[str, Any]] = None,
        search_method: str = "grid",
        n_iter: int = 50,
        cv: int = 5,
        data_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Fine-tune model hyperparameters."""
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
                    "search_method": search_method,
                    "n_iter": n_iter,
                    "cv": cv,
                    **(data_context or {}),
                },
                hyperparameters=param_grid,
                status="running",
                started_at=utcnow_naive(),
            )
            db.add(training_run)
            db.commit()

            # Get base model
            base_model = self._get_base_model(model.model_type, model.hyperparameters)

            # Perform hyperparameter search
            effective_cv = max(2, min(cv, len(X_train)))
            if search_method == "grid":
                search = GridSearchCV(
                    base_model,
                    param_grid or self._get_default_param_grid(model.model_type),
                    cv=effective_cv,
                    scoring='neg_mean_squared_error',
                    n_jobs=-1,
                )
            else:
                search = RandomizedSearchCV(
                    base_model,
                    param_grid or self._get_default_param_grid(model.model_type),
                    n_iter=n_iter,
                    cv=effective_cv,
                    scoring='neg_mean_squared_error',
                    n_jobs=-1,
                    random_state=42,
                )

            # Fit search
            search.fit(X_train, y_train)

            # Update model with best parameters
            model.hyperparameters = search.best_params_
            model.status = ModelStatus.TRAINED
            model.trained_at = utcnow_naive()
            model.training_samples = len(X_train)
            if data_context:
                model.features = data_context.get("features")
                model.target_variable = data_context.get("target_column")

            # Update training run
            training_run.status = "completed"
            training_run.completed_at = utcnow_naive()
            training_run.training_loss = -search.best_score_
            training_run.validation_metrics = {
                "best_score": search.best_score_,
                "best_params": search.best_params_,
                "cv_results": {
                    "mean_test_score": search.cv_results_['mean_test_score'].tolist(),
                    "std_test_score": search.cv_results_['std_test_score'].tolist(),
                },
            }

            db.commit()

            # Save model artifact
            # Safety: joblib used for local ML model serialization only.
            # Models are created internally, not loaded from untrusted sources.
            model_path = os.path.join(self.models_dir, f"{model_id}.joblib")
            joblib.dump(search.best_estimator_, model_path)
            model.model_path = model_path
            model.model_size_bytes = os.path.getsize(model_path)
            db.commit()

            return {
                "model_id": model_id,
                "best_params": search.best_params_,
                "best_score": search.best_score_,
                "cv_results": training_run.validation_metrics,
                "model_path": model_path,
            }

        except Exception as e:
            logger.error(f"Error fine-tuning model {model_id}: {e}")
            if model:
                model.status = ModelStatus.DRAFT
                db.commit()
            raise
        finally:
            db.close()

    async def optimize_thresholds(
        self,
        model_id: str,
        X_val: np.ndarray,
        y_val: np.ndarray,
        thresholds: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Optimize decision thresholds for classification models."""
        db = SessionLocal()
        try:
            model = db.query(Model).filter(Model.id == model_id).first()
            if not model:
                raise ValueError(f"Model {model_id} not found")

            # Load model
            if not model.model_path or not os.path.exists(model.model_path):
                raise ValueError(f"Model artifact not found for {model_id}")

            # Safety: Loading locally-created model artifact only.
            trained_model = joblib.load(model.model_path)

            # Get predictions
            if hasattr(trained_model, 'predict_proba'):
                y_proba = trained_model.predict_proba(X_val)[:, 1]
            else:
                raise ValueError("Model does not support probability predictions")

            # Test different thresholds
            if thresholds is None:
                thresholds = np.arange(0.1, 0.9, 0.05).tolist()

            results = []
            for threshold in thresholds:
                y_pred = (y_proba >= threshold).astype(int)

                # Calculate metrics
                tp = np.sum((y_pred == 1) & (y_val == 1))
                fp = np.sum((y_pred == 1) & (y_val == 0))
                tn = np.sum((y_pred == 0) & (y_val == 0))
                fn = np.sum((y_pred == 0) & (y_val == 1))

                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
                accuracy = (tp + tn) / len(y_val)

                results.append({
                    "threshold": threshold,
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1,
                    "accuracy": accuracy,
                    "tp": int(tp),
                    "fp": int(fp),
                    "tn": int(tn),
                    "fn": int(fn),
                })

            # Find best threshold by F1 score
            best_result = max(results, key=lambda x: x["f1_score"])

            return {
                "model_id": model_id,
                "thresholds_tested": len(results),
                "best_threshold": best_result["threshold"],
                "best_f1_score": best_result["f1_score"],
                "all_results": results,
            }

        except Exception as e:
            logger.error(f"Error optimizing thresholds for model {model_id}: {e}")
            raise
        finally:
            db.close()

    def _get_base_model(self, model_type: str, hyperparameters: Optional[Dict] = None):
        """Get base model instance."""
        from sklearn.linear_model import LinearRegression
        from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

        params = hyperparameters or {}

        if model_type == "linear_regression":
            return LinearRegression(**params)
        elif model_type == "random_forest":
            return RandomForestRegressor(**params)
        elif model_type == "xgboost":
            try:
                import xgboost as xgb
            except ImportError as exc:
                raise ValueError(
                    "XGBoost model type requires the optional xgboost dependency"
                ) from exc
            return xgb.XGBRegressor(**params)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

    def _get_default_param_grid(self, model_type: str) -> Dict[str, Any]:
        """Get default parameter grid for hyperparameter search."""
        if model_type == "linear_regression":
            return {
                "fit_intercept": [True, False],
            }
        elif model_type == "random_forest":
            return {
                "n_estimators": [50, 100, 200],
                "max_depth": [5, 10, 15, None],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4],
            }
        elif model_type == "xgboost":
            return {
                "n_estimators": [50, 100, 200],
                "max_depth": [3, 6, 9],
                "learning_rate": [0.01, 0.1, 0.2],
                "subsample": [0.6, 0.8, 1.0],
                "colsample_bytree": [0.6, 0.8, 1.0],
            }
        else:
            return {}


# Global service instance
model_fine_tuning_service = ModelFineTuningService()
