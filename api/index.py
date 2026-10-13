import os
import sys

# Ensure project root directory is on sys.path so 'app' and 'config' can be imported reliably on Vercel
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

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

if __name__ == "__main__":
    app.run(debug=True)
