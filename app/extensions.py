"""Flask extension instances initialized without app context."""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect

# Database ORM
db = SQLAlchemy()

# Database Migrations
migrate = Migrate()

# User Session Management
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please sign in to access this page."
login_manager.login_message_category = "warning"

# CSRF Protection
csrf = CSRFProtect()

# Security Headers (Talisman)
talisman = Talisman()

# Rate Limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)
