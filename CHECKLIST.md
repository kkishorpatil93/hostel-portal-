# StayNest PG — Implementation Checklist

## Done
- [x] Phase 1: Workspace initialization at `pg-management-website/`
- [x] Phase 1: Python virtual environment (`.venv`) created with all dependencies
- [x] Phase 1: Dependency files (`requirements.txt`, `requirements-dev.txt`)
- [x] Phase 1: Environment configurations (`.env.example`, `.env`, `config.py` for Dev/Testing/Prod)
- [x] Phase 1: Agent rules & engineering standards (`AGENTS.md`, `.agent/rules/rules.md`)
- [x] Phase 1: Implementation Plan and Task List artifacts created
- [x] Phase 2: Application Factory (`create_app`) and Flask extensions configured
- [x] Phase 2: All 17 domain database models designed, mapped, and typed with SQLAlchemy 2.x
- [x] Phase 2: Alembic database migrations initialized and schema upgraded (`flask db upgrade`)
- [x] Phase 2: Flask CLI commands implemented (`create-owner`, `seed-demo`, `generate-rent`)
- [x] Phase 2: Liveness & readiness health check endpoint implemented (`/healthz`)
- [x] Phase 2: Custom error handlers (400, 403, 404, 500) and base responsive layouts
- [x] Phase 2: Automated testing suite (14 pytest tests, 100% pass rate)
- [x] Phase 2: Security scanning via `bandit` (0 issues) and `pip-audit` (0 vulnerabilities)
- [x] Phase 2: Linting and formatting via `ruff` (clean pass)

## In Progress
- [ ] Phase 3: Design system completion, base layouts, public pages (home, rooms, room details, amenities, about, contact, FAQ) reading real database records, fully responsive.

## Remaining
- [ ] Phase 4: Secure registration, login, logout, password reset, role-based access, rate limiting, security headers.
- [ ] Phase 5: Owner dashboard, property/room/bed/photo management, settings.
- [ ] Phase 6: Booking requests, owner decisions, safe allocation service, check-in/check-out.
- [ ] Phase 7: Tenant dashboard, profile, booking status, notices.
- [ ] Phase 8: Rent charges, payments, deposits, receipts, complaints, notices, tour requests, notifications, reports.
- [ ] Phase 9: Advanced features (rent automation, receipts & CSV exports, Razorpay sandbox, notifications adapter).
- [ ] Phase 10: Hardening, full test suite, accessibility/Lighthouse pass, security scan.
- [ ] Phase 11: Deployment files, documentation, backup guide, final checklist and handover summary.

## Not Verified (Pending Local Environment/Third-Party Configuration)
- Live external SMTP email sending (console/log backend used in dev)
- Live Razorpay production payment webhook (manual Cash/UPI recording verified)
- Production cloud deployment on Render/Railway/VPS (local Waitress/WSGI verified)

## Known Issues
- None.
