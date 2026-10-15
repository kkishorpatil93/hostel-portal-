import os
import secrets
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

IS_VERCEL = bool(
    os.getenv("VERCEL")
    or os.getenv("VERCEL_ENV")
    or os.getenv("VERCEL_REGION")
    or os.getenv("NOW_REGION")
    or "VERCEL" in os.environ
)


class Config:
    """Base configuration with production-grade defaults."""

    # Project directories
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    if IS_VERCEL:
        INSTANCE_DIR = "/tmp/instance"
        UPLOAD_FOLDER = "/tmp/uploads"
        PRIVATE_UPLOAD_FOLDER = "/tmp/private_uploads"
        DEFAULT_DB_PATH = "sqlite:////tmp/staynest.db"
    else:
        INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
        UPLOAD_FOLDER = os.path.join(BASE_DIR, os.getenv("UPLOAD_FOLDER", "app/static/uploads"))
        PRIVATE_UPLOAD_FOLDER = os.path.join(
            BASE_DIR, os.getenv("PRIVATE_UPLOAD_FOLDER", "instance/private_uploads")
        )
        DEFAULT_DB_PATH = f"sqlite:///{os.path.join(INSTANCE_DIR, 'staynest.db')}"

    # Safely create directories without crashing on read-only environments
    try:
        os.makedirs(INSTANCE_DIR, exist_ok=True)
    except (OSError, PermissionError):
        pass

    # Core Security
    SECRET_KEY = os.getenv("SECRET_KEY", "staynest-default-secret-key-min-32-chars-long")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour CSRF token expiration

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", DEFAULT_DB_PATH)

    # Fix for Postgres URLs (e.g. Supabase, Render, Heroku)
    if SQLALCHEMY_DATABASE_URI:
        if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
                "postgres://", "postgresql+psycopg2://", 1
            )
        elif SQLALCHEMY_DATABASE_URI.startswith("postgresql://") and not SQLALCHEMY_DATABASE_URI.startswith("postgresql+"):
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
                "postgresql://", "postgresql+psycopg2://", 1
            )

    # Session Management
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1")

    # File Uploads
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(10 * 1024 * 1024)))  # 10 MB
    ALLOWED_EXTENSIONS = ("png", "jpg", "jpeg", "webp", "pdf")

    # Regional Defaults (India)
    CURRENCY_SYMBOL = os.getenv("CURRENCY_SYMBOL", "₹")
    CURRENCY_CODE = os.getenv("CURRENCY_CODE", "INR")
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
    DATE_FORMAT = os.getenv("DATE_FORMAT", "%d-%b-%Y")

    # Operational Defaults
    DEFAULT_RENT_DUE_DAY = int(os.getenv("DEFAULT_RENT_DUE_DAY", "5"))
    DEFAULT_GRACE_DAYS = int(os.getenv("DEFAULT_GRACE_DAYS", "3"))
    DEFAULT_NOTICE_PERIOD_DAYS = int(os.getenv("DEFAULT_NOTICE_PERIOD_DAYS", "30"))
    DEFAULT_SECURITY_DEPOSIT_MONTHS = int(os.getenv("DEFAULT_SECURITY_DEPOSIT_MONTHS", "1"))

    # Rate Limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URI = "memory://"

    # AI Feature Flag
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing configuration (isolated in-memory or test SQLite)."""

    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production configuration with strict verification and serverless compatibility."""

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"

    @classmethod
    def init_app(cls, app):
        insecure_keys = [
            "insecure-dev-fallback-key-replace-in-env",
            "staynest-dev-secret-key-32-character-random-dev-only",
            "generate-a-strong-secret-key-min-32-chars-for-production",
        ]
        secret = os.getenv("SECRET_KEY", "")

        # In serverless preview environments (like Vercel), generate a fallback key so preview doesn't 500
        if not secret or secret in insecure_keys or len(secret) < 32:
            if IS_VERCEL or os.getenv("VERCEL"):
                app.config["SECRET_KEY"] = secrets.token_hex(32)
                return

            raise ValueError(
                "CRITICAL SECURITY ERROR: SECRET_KEY must be set to a secure, random string "
                "of at least 32 characters in production environments."
            )


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
