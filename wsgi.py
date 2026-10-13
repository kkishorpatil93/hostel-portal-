"""Production WSGI entrypoint for StayNest PG platform."""

import os

from app import create_app

app = create_app(os.getenv("FLASK_ENV", "production"))

if __name__ == "__main__":
    from waitress import serve

    port = int(os.getenv("PORT", "5000"))
    print(f"Starting Waitress WSGI server on http://0.0.0.0:{port}")
    serve(app, host="0.0.0.0", port=port)
