# StayNest PG — Workspace Rules

1. Always follow the Flask application factory pattern (`create_app`).
2. Keep business logic in `app/services/` (e.g., `allocation.py`, `billing.py`), separate from HTTP route handlers.
3. Monetary amounts must use SQLAlchemy `Numeric(10,2)`.
4. Always enforce server-side validation and authorization.
5. All sensitive uploads (like tenant ID proofs) must be stored in private storage and served only through authenticated routes.
6. Local development runs on SQLite (`instance/staynest.db`); production targets PostgreSQL.
7. Run tests with `pytest` after making modifications.
