"""Application factory for StayNest PG platform."""

import os
from datetime import UTC, datetime

from flask import Flask, jsonify, render_template
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix

from app.extensions import csrf, db, limiter, login_manager, migrate, talisman
from app.models.user import User
from config import config_by_name


def format_inr(value):
    """Format decimal or integer into Indian currency format (e.g., 12,500.00)."""
    if value is None:
        return "0.00"
    try:
        float_val = float(value)
        s = f"{float_val:.2f}"
        integer_part, decimal_part = s.split(".")
        if len(integer_part) > 3:
            last3 = integer_part[-3:]
            rest = integer_part[:-3]
            groups = []
            while len(rest) > 2:
                groups.insert(0, rest[-2:])
                rest = rest[:-2]
            if rest:
                groups.insert(0, rest)
            groups.append(last3)
            formatted_int = ",".join(groups)
        else:
            formatted_int = integer_part
        return f"{formatted_int}.{decimal_part}"
    except (ValueError, TypeError):
        return str(value)


def format_date_ist(dt_val, fmt="%d-%b-%Y"):
    """Format datetime or date object into UI standard DD-MMM-YYYY."""
    if not dt_val:
        return "-"
    if isinstance(dt_val, datetime):
        return dt_val.strftime(fmt)
    if hasattr(dt_val, "strftime"):
        return dt_val.strftime(fmt)
    return str(dt_val)


def create_app(config_name=None):
    """Create and configure the Flask application instance."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development").lower()

    app_dir = os.path.abspath(os.path.dirname(__file__))
    app = Flask(
        __name__,
        template_folder=os.path.join(app_dir, "templates"),
        static_folder=os.path.join(app_dir, "static"),
    )
    config_class = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_class)

    # Initialize production security guard if applicable
    if hasattr(config_class, "init_app"):
        config_class.init_app(app)

    # ProxyFix for reverse proxies (Vercel, Render, Nginx)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Strip /api/index prefix if Vercel internal rewrite passed the destination path
    class StripVercelPrefixMiddleware:
        def __init__(self, wsgi_app):
            self.wsgi_app = wsgi_app

        def __call__(self, environ, start_response):
            path_info = environ.get("PATH_INFO", "")
            if path_info.startswith("/api/index"):
                new_path = path_info[len("/api/index"):] or "/"
                environ["PATH_INFO"] = new_path
            return self.wsgi_app(environ, start_response)

    app.wsgi_app = StripVercelPrefixMiddleware(app.wsgi_app)

    # Ensure required directories exist (failsafe on read-only serverless filesystems)
    try:
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        os.makedirs(app.config["PRIVATE_UPLOAD_FOLDER"], exist_ok=True)
    except (OSError, PermissionError):
        pass

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Security Headers with Talisman
    csp = {
        "default-src": ["'self'"],
        "script-src": [
            "'self'",
            "'unsafe-inline'",
            "'unsafe-eval'",
            "https://cdn.jsdelivr.net",
            "https://cdnjs.cloudflare.com",
            "https://unpkg.com",
        ],
        "style-src": [
            "'self'",
            "'unsafe-inline'",
            "https://fonts.googleapis.com",
            "https://cdnjs.cloudflare.com",
            "https://cdn.jsdelivr.net",
        ],
        "font-src": ["'self'", "https://fonts.gstatic.com", "https://cdnjs.cloudflare.com"],
        "img-src": ["'self'", "data:", "https:"],
        "frame-src": ["'self'", "https://www.google.com"],
    }

    talisman.init_app(
        app,
        force_https=False,
        content_security_policy=csp,
        content_security_policy_nonce_in=["script-src"],
    )

    # Register Login Manager User Loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from app.api import api_bp
    from app.auth import auth_bp
    from app.owner import owner_bp
    from app.public import public_bp
    from app.tenant import tenant_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(owner_bp)
    app.register_blueprint(tenant_bp)
    app.register_blueprint(api_bp)

    # Register CLI commands
    from app import cli
    cli.register_cli_commands(app)

    # Auto-initialize database tables and demo seed on fresh/serverless environments
    with app.app_context():
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            if not inspector.has_table("properties"):
                db.create_all()
                from app.cli import seed_demo_data
                seed_demo_data(app)
        except Exception as exc:  # noqa: BLE001
            app.logger.warning(f"Database auto-init skipped: {exc}")

    # Context Processors & Filters
    @app.context_processor
    def inject_global_template_vars():
        from app.models.settings import SiteSetting
        return {
            "current_year": datetime.now(UTC).year,
            "currency_symbol": app.config.get("CURRENCY_SYMBOL", "₹"),
            "site_title": SiteSetting.get_value("site_title", "StayNest PG"),
            "contact_phone": SiteSetting.get_value("contact_phone", "+91 98765 43210"),
            "contact_email": SiteSetting.get_value("contact_email", "staynestpg@example.com"),
        }

    app.jinja_env.filters["inr"] = format_inr
    app.jinja_env.filters["date_fmt"] = format_date_ist

    # Custom Error Handlers
    @app.errorhandler(400)
    def bad_request_error(e):
        return render_template("errors/400.html", error=e), 400

    @app.errorhandler(403)
    def forbidden_error(e):
        return render_template("errors/403.html", error=e), 403

    @app.errorhandler(404)
    def not_found_error(e):
        return render_template("errors/404.html", error=e), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        db.session.rollback()
        return render_template("errors/500.html", error=e), 500

    # Liveness & Readiness Health Endpoint
    @app.route("/healthz")
    def health_check():
        db_status = "ok"
        try:
            db.session.execute(text("SELECT 1"))
        except Exception as exc:  # noqa: BLE001
            db_status = f"unhealthy: {exc!s}"

        is_healthy = db_status == "ok"
        response_data = {
            "status": "healthy" if is_healthy else "unhealthy",
            "database": db_status,
            "version": "1.0.0",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        return jsonify(response_data), (200 if is_healthy else 503)

    return app
