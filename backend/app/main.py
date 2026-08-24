from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.api import stocks, search, models, recommendations, user, governance, intelligence
from app.core.config import settings
from app.core.database import init_db
from app.services.intelligence_monitoring_service import intelligence_monitoring_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("=" * 50)
    print("Starting Quant Trading Advisor API...")
    print(f"Database: {settings.DATABASE_URL}")
    print("=" * 50)

    # Initialize database tables
    init_db()
    print("✓ Database initialized")
    intelligence_monitoring_service.start()
    print("✓ Intelligence monitor scheduler started")

    yield

    # Shutdown
    await intelligence_monitoring_service.stop()
    print("Shutting down Quant Trading Advisor API...")


# Create FastAPI app
app = FastAPI(
    title="Quant Trading Advisor API",
    description="量化交易建议系统 API",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stocks.router)
app.include_router(search.router)
app.include_router(models.router)
app.include_router(recommendations.router)
app.include_router(user.router)
app.include_router(governance.router)
app.include_router(intelligence.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Quant Trading Advisor API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2026-08-20T00:00:00Z",
    }


@app.get("/api/v1/status")
async def api_status():
    """API status endpoint."""
    return {
        "api_version": "v1",
        "status": "operational",
        "features": {
            "stock_search": True,
            "recommendations": True,
            "model_training": True,
            "governance": True,
        },
    }


# Backward-compatible import path. The product has one canonical runtime so
# legacy `uvicorn app.main:app` commands cannot expose stale health or routes.
from app.main_ui import app as app  # noqa: E402,F401
