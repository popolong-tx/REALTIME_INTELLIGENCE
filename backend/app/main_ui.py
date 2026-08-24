from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import os

from app.api import stocks, search, models, recommendations, user, governance, platform, intelligence
from app.api import broker, webhooks
from app.core.config import settings
from app.core.database import init_db
from app.services.intelligence_monitoring_service import intelligence_monitoring_service
from app.services.capability_status_service import build_readiness_report

logger = logging.getLogger(__name__)

UI_RUNTIME_VERSION = "2026.08.24.14"
APP_STARTED_AT = datetime.now(timezone.utc).isoformat()

# Resolve the product shell from the repository root so the same layout works
# locally and in the unified container image.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend", "public")
FRONTEND_ASSETS_DIR = os.path.join(FRONTEND_DIR, "assets")
INDEX_FILE = os.path.join(FRONTEND_DIR, "index.html")

if not os.path.isfile(INDEX_FILE) or not os.path.isdir(FRONTEND_ASSETS_DIR):
    raise RuntimeError(
        "Frontend product shell is incomplete. Expected index.html and assets/ "
        f"under {FRONTEND_DIR}."
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("=" * 50)
    print("Starting Quant Trading Advisor API...")
    print(f"Runtime: {UI_RUNTIME_VERSION}")
    print(f"Database: {settings.DATABASE_URL}")
    print(f"Frontend: {FRONTEND_DIR}")
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
    version=UI_RUNTIME_VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the dependency-free product shell assets. Keeping these files behind the
# same origin as the API avoids hard-coded localhost URLs and works in containers.
app.mount(
    "/assets",
    StaticFiles(directory=FRONTEND_ASSETS_DIR),
    name="frontend-assets",
)

# Include routers
app.include_router(stocks.router)
app.include_router(search.router)
app.include_router(models.router)
app.include_router(recommendations.router)
app.include_router(user.router)
app.include_router(governance.router)
app.include_router(platform.router)
app.include_router(intelligence.router)
app.include_router(broker.router)
app.include_router(webhooks.router)


@app.get("/")
async def root():
    """Serve the product shell without caching a stale entrypoint."""
    return FileResponse(INDEX_FILE, headers={"Cache-Control": "no-store"})


@app.get("/ui")
async def ui():
    """Serve the UI."""
    return FileResponse(INDEX_FILE, headers={"Cache-Control": "no-store"})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    readiness = await build_readiness_report()
    return {
        **readiness,
        "runtime_version": UI_RUNTIME_VERSION,
        "started_at": APP_STARTED_AT,
    }


@app.get("/api/v1/status")
async def api_status():
    """API status endpoint."""
    readiness = await build_readiness_report()
    return {
        "api_version": "v1",
        "runtime_version": UI_RUNTIME_VERSION,
        "started_at": APP_STARTED_AT,
        "status": readiness["status"],
        "frontend": {
            "entrypoint": "frontend/public/index.html",
            "assets_mounted": True,
        },
        "features": readiness["modules"],
        "checks": readiness["checks"],
        "integrations": readiness["integrations"],
    }
