import os
import sys

# Ensure project root directory is on sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from app import create_app

    is_serverless = bool(
        os.getenv("VERCEL")
        or os.getenv("VERCEL_ENV")
        or os.getenv("VERCEL_REGION")
        or os.getenv("NOW_REGION")
    )
    default_env = "production" if is_serverless else "development"
    env_name = os.getenv("FLASK_ENV", default_env)

    app = create_app(env_name)
    handler = app

except Exception:  # noqa: BLE001
    import traceback

    tb = traceback.format_exc()
    print("FATAL FLASK INITIALIZATION ERROR:\n", tb, file=sys.stderr)

    from flask import Flask, Response

    app = Flask(__name__)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def startup_fallback(path):
        return Response(
            f"<!DOCTYPE html><html><head><title>Startup Error</title></head><body>"
            f"<h2>StayNest Platform - Server Startup Error</h2>"
            f"<pre style='background:#f4f4f4;padding:16px;border-radius:8px;font-family:monospace;'>{tb}</pre>"
            f"</body></html>",
            status=500,
            mimetype="text/html",
        )

    handler = app

if __name__ == "__main__":
    app.run(debug=True)
