"""Development server and CLI entrypoint for StayNest PG."""

import os
from app import create_app

env_name = os.getenv("FLASK_ENV", "development").lower()
app = create_app(env_name)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)
