# StayNest PG — Agent Rules & Engineering Standards

## 1. Core Principles
- **No Untested Work**: Never claim something works unless you ran it and saw it pass. If something cannot be verified in the local environment, explicitly declare "NOT VERIFIED" along with exact reproduction steps.
- **No Fake Data in Production**: All seed data for development must be clearly marked as demo/sample (e.g., `demo.tenant@example.com`, `Sample Bed A`). Never hardcode mock responses in service layers.
- **Do Not Break Existing Code**: Always inspect existing files before editing. Do not overwrite or delete existing files without clear justification.

## 2. Technology Stack & Coding Standards
- **Backend**: Python 3.11+ / 3.13, Flask application factory pattern (`create_app`), Flask-SQLAlchemy, Flask-Migrate (Alembic), Flask-Login, Flask-WTF (CSRF + forms), Flask-Limiter, Flask-Talisman.
- **Database**: SQLite for local development (`instance/staynest.db`); must execute identically on PostgreSQL in production. Use SQLAlchemy `Numeric(10,2)` for all monetary fields—never float.
- **Frontend**: Custom CSS3 design system with CSS custom properties (variables), mobile-first responsive architecture (desktop 1440px, tablet 768px, mobile 375px), vanilla JavaScript, optional HTMX/Alpine.js without heavy npm build steps.
- **Regional Settings**: Defaults set for India (Currency: ₹ INR, Timezone: Asia/Kolkata stored as UTC, Dates: DD-MMM-YYYY, Phone: Indian mobile format). All defaults must be configurable.

## 3. Security Requirements
- **Passwords**: Werkzeug Scrypt/PBKDF2 hashing; strict minimum strength rules.
- **Authorization**: Enforce at the server on every protected route. Never trust client-sent role, price, amount, or user_id. Tenants must never access owner routes or other tenants' records. Return 404 (not 403) for unauthorized cross-tenant records to avoid ID enumeration.
- **CSRF**: Enforced on every state-changing route (forms, AJAX, HTMX, logout).
- **Rate Limiting**: Enforced on authentication routes and public enquiry forms.
- **File Uploads**: Restrict to allowed extensions (`.jpg`, `.jpeg`, `.png`, `.webp`, `.pdf`). Verify file headers using Pillow. Strip EXIF metadata. Store private tenant ID proofs in private folders outside the static directory, served only through authenticated routes.
- **Audit Logging**: Maintain tamper-evident `ActivityLog` records for critical actions (allocations, payments, check-ins, status transitions).
