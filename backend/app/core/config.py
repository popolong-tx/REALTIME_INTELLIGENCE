from pydantic_settings import BaseSettings
from typing import Optional
import os

# Get the base directory (backend folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Quant Trading Advisor"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Database - SQLite for local development
    DATABASE_URL: str = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'quant_advisor.db')}"

    # Redis - use fake redis if not available
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 10

    # OCI Generative AI / xAI models
    OCI_CONFIG_PATH: Optional[str] = None
    OCI_REGION: str = "us-chicago-1"
    OCI_GENAI_API_KEY: Optional[str] = None
    OCI_GENAI_BASE_URL: Optional[str] = None
    OCI_GROK_MODEL_ID: str = "xai.grok-4.3"
    OCI_GROK_MULTI_AGENT_MODEL_ID: str = "xai.grok-4.20-multi-agent"

    # Legacy direct-xAI settings. New real-time research must use the OCI
    # Responses API above; these names remain for backward compatibility.
    XAI_API_KEY: Optional[str] = None
    XAI_MODEL_ID: str = "xai.grok-4.3"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Execution safety. The demo is research and simulation only. Live broker
    # mutations require both controls to be explicitly changed server-side.
    EXECUTION_MODE: str = "simulation_only"
    BROKER_LIVE_TRADING_ENABLED: bool = False

    # Data Sources
    YAHOO_FINANCE_ENABLED: bool = True
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    TUSHARE_TOKEN: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

# Ensure data directory exists
os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)
