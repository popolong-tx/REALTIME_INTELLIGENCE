from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
import uuid

from app.core.database import Base
from app.models.platform_operations import utcnow_naive


class ModelStatus(str, Enum):
    DRAFT = "draft"
    TRAINING = "training"
    TRAINED = "trained"
    VALIDATING = "validating"
    VALIDATED = "validated"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPLOYED = "deployed"


class ModelType(str, Enum):
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    LSTM = "lstm"
    TRANSFORMER = "transformer"
    ENSEMBLE = "ensemble"


class Model(Base):
    """Model registry for trained models."""

    __tablename__ = "models"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String)
    model_type = Column(SQLEnum(ModelType), nullable=False)
    version = Column(String, nullable=False)
    status = Column(SQLEnum(ModelStatus), default=ModelStatus.DRAFT)

    # Model configuration
    hyperparameters = Column(JSON)
    features = Column(JSON)
    target_variable = Column(String)

    # Training data
    training_data_start = Column(DateTime)
    training_data_end = Column(DateTime)
    training_samples = Column(Integer)

    # Performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    total_return = Column(Float)

    # Validation
    validation_metrics = Column(JSON)
    backtest_results = Column(JSON)

    # Model artifacts
    model_path = Column(String)
    model_size_bytes = Column(Integer)

    # Governance
    created_by = Column(String)
    approved_by = Column(String)
    approved_at = Column(DateTime)
    rejection_reason = Column(String)

    # Environment
    environment = Column(String, default="research")  # research, training, validation, production

    # Timestamps
    created_at = Column(DateTime, default=utcnow_naive)
    updated_at = Column(DateTime, default=utcnow_naive, onupdate=utcnow_naive)
    trained_at = Column(DateTime)

    # Relationships
    training_runs = relationship("TrainingRun", back_populates="model")
    deployments = relationship("ModelDeployment", back_populates="model")


class TrainingRun(Base):
    """Individual training run for a model."""

    __tablename__ = "training_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String, ForeignKey("models.id"), nullable=False)

    # Run configuration
    run_config = Column(JSON)
    hyperparameters = Column(JSON)

    # Training data
    data_source = Column(String)
    data_hash = Column(String)  # Hash of training data for reproducibility

    # Metrics
    training_loss = Column(Float)
    validation_loss = Column(Float)
    epochs = Column(Integer)
    training_time_seconds = Column(Float)

    # Status
    status = Column(String, default="pending")  # pending, running, completed, failed
    error_message = Column(String)

    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=utcnow_naive)

    # Relationships
    model = relationship("Model", back_populates="training_runs")


class ModelDeployment(Base):
    """Model deployment tracking."""

    __tablename__ = "model_deployments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String, ForeignKey("models.id"), nullable=False)

    # Deployment configuration
    environment = Column(String, nullable=False)  # staging, production
    alias = Column(String)  # champion, challenger
    traffic_percentage = Column(Float, default=100.0)

    # Status
    is_active = Column(Boolean, default=True)

    # Performance tracking
    requests_count = Column(Integer, default=0)
    average_latency_ms = Column(Float)
    error_rate = Column(Float)

    # Timestamps
    deployed_at = Column(DateTime, default=utcnow_naive)
    deactivated_at = Column(DateTime)

    # Relationships
    model = relationship("Model", back_populates="deployments")


class ModelAlias(Base):
    """Model alias management (champion/challenger)."""

    __tablename__ = "model_aliases"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    alias = Column(String, nullable=False, unique=True)  # champion, challenger_1, etc.
    model_id = Column(String, ForeignKey("models.id"), nullable=False)

    # Alias configuration
    is_active = Column(Boolean, default=True)
    traffic_percentage = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=utcnow_naive)
    updated_at = Column(DateTime, default=utcnow_naive, onupdate=utcnow_naive)

    # Relationships
    model = relationship("Model")


class Experiment(Base):
    """Experiment tracking for model research."""

    __tablename__ = "experiments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String)

    # Experiment configuration
    hypothesis = Column(String)
    protocol = Column(JSON)

    # Results
    metrics = Column(JSON)
    conclusions = Column(String)

    # Status
    status = Column(String, default="planning")  # planning, running, completed, archived

    # Timestamps
    created_at = Column(DateTime, default=utcnow_naive)
    updated_at = Column(DateTime, default=utcnow_naive, onupdate=utcnow_naive)
    completed_at = Column(DateTime)

    # Creator
    created_by = Column(String)
