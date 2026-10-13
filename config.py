import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration with production-grade defaults."""

    # Project directories
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
    os.makedirs(INSTANCE_DIR, exist_ok=True)

    # Core Security
    SECRET_KEY = os.getenv("SECRET_KEY", "insecure-dev-fallback-key-replace-in-env")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour CSRF token expiration

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{os.path.join(INSTANCE_DIR, 'staynest.db')}"
    )

    # Fix for Postgres URLs starting with postgres:// (e.g. Render / Heroku)
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "postgres://", "postgresql+psycopg2://", 1
        )

    # Session Management
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1")

    # File Uploads
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))  # 10 MB
    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.getenv("UPLOAD_FOLDER", "app/static/uploads"))
    PRIVATE_UPLOAD_FOLDER = os.path.join(
        BASE_DIR, os.getenv("PRIVATE_UPLOAD_FOLDER", "instance/private_uploads")
    )
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}

    # Regional Defaults (India)
    CURRENCY_SYMBOL = os.getenv("CURRENCY_SYMBOL", "₹")
    CURRENCY_CODE = os.getenv("CURRENCY_CODE", "INR")
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
    DATE_FORMAT = os.getenv("DATE_FORMAT", "%d-%b-%Y")

    # Operational Defaults
    DEFAULT_RENT_DUE_DAY = int(os.getenv("DEFAULT_RENT_DUE_DAY", 5))
    DEFAULT_GRACE_DAYS = int(os.getenv("DEFAULT_GRACE_DAYS", 3))
    DEFAULT_NOTICE_PERIOD_DAYS = int(os.getenv("DEFAULT_NOTICE_PERIOD_DAYS", 30))
    DEFAULT_SECURITY_DEPOSIT_MONTHS = int(os.getenv("DEFAULT_SECURITY_DEPOSIT_MONTHS", 1))

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
    """Production configuration with strict verification."""

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Strict"

    @classmethod
    def init_app(cls, app):
        # Prevent starting production with weak or default secret key
        insecure_keys = [
            "insecure-dev-fallback-key-replace-in-env",
            "staynest-dev-secret-key-32-character-random-dev-only",
            "generate-a-strong-secret-key-min-32-chars-for-production",
        ]
        secret = os.getenv("SECRET_KEY", "")
        if not secret or secret in insecure_keys or len(secret) < 32:
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
