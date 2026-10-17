import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "libraflow-dev-secret-key-change-in-prod-xyz789")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "database" / "libraflow.db"))
    LOAN_PERIOD_DAYS = int(os.environ.get("LOAN_PERIOD_DAYS", "14"))
    FINE_PER_DAY = float(os.environ.get("FINE_PER_DAY", "1.00"))
    TESTING = False
    DEBUG = False


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class TestingConfig(Config):
    """Testing configuration with separate in-memory or temp SQLite DB."""
    TESTING = True
    DEBUG = True
    SECRET_KEY = "test-secret-key-libraflow"
    DATABASE_PATH = ":memory:"


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # Ensure SECRET_KEY is set in environment for production
    SECRET_KEY = os.environ.get("SECRET_KEY", "prod-libraflow-secret-fallback-key-998877")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
