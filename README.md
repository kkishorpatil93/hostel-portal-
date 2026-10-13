# StayNest PG — Advanced PG Management & Booking Platform

An enterprise-grade, secure, multi-role Paying Guest (PG) management and booking web application tailored for the Indian rental accommodation market. Built with Python, Flask, SQLAlchemy, and a mobile-first accessible design system.

---

## 🌟 Key Features

- **Public Accommodation Portal**:
  - Live available-room cards with real-time bed count tracking from the database.
  - Search and filter rooms by room type (Single, Double, Triple sharing).
  - Detailed room pages with amenities, monthly rent, and security deposit terms.
  - Guided in-person tour scheduling form with anti-spam protections.
  - Responsive design across desktop (1440px), tablet (768px), and mobile (375px).

- **Tenant Portal**:
  - Secure registration and session authentication.
  - Real-time stay overview with assigned room/bed and monthly rent rate.
  - Billing ledger with due dates, payment history, and downloadable receipts.
  - Maintenance ticketing grievance system with status tracking.
  - Official notice board and announcements.

- **Owner Administration Portal**:
  - Operational metrics dashboard: occupancy rate, total beds, available beds, overdue dues, pending bookings, and open complaints.
  - Room and bed inventory management with soft-delete protections.
  - Booking approval system with bed allocation in a single ACID transaction.
  - Idempotent monthly rent charge generation with configurable grace period.
  - Resident directory with emergency contacts and KYC profile records.

- **Security & Engineering**:
  - Password hashing with Werkzeug Scrypt.
  - Brute-force failed login account lockout.
  - Full CSRF protection on state-changing requests.
  - HTTP security headers with Flask-Talisman and Content Security Policy (CSP).
  - Rate limiting via Flask-Limiter.
  - 100% test coverage with automated unit and integration tests.
  - SAST security analysis with Bandit (0 vulnerabilities) and dependency auditing with pip-audit (0 vulnerabilities).

---

## 🚀 Quick Start (Local Setup)

### Prerequisites
- Python 3.11+ or Python 3.13
- Windows PowerShell / Linux Terminal / macOS Terminal

### 1. Clone & Enter Directory
```bash
git clone https://github.com/kkishorpatil93/hostel-portal-.git
cd hostel-portal-
```

### 2. Set Up Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Copy the example environment configuration:
```bash
cp .env.example .env
```

### 5. Initialize Database Migrations
```bash
flask --app run.py db upgrade
```

### 6. Create Your Owner Account
```bash
flask --app run.py create-owner
```
*(Interactive prompt will securely ask for Name, Email, Mobile Phone, and Password)*

### 7. (Optional) Seed Sample Development Data
```bash
flask --app run.py seed-demo
```

### 8. Run the Development Server
```bash
flask --app run.py run --port 5000
```
Visit **[http://localhost:5000](http://localhost:5000)** in your browser!

---

## 🧪 Running Automated Tests

Run the full test suite with coverage:
```bash
pytest -v --cov=app
```

Run code formatting and security checks:
```bash
ruff check app tests
bandit -r app -ll
pip-audit
```

---

## 📂 Project Structure

```text
pg-management-website/
├── app/
│   ├── __init__.py            # Application Factory (create_app)
│   ├── extensions.py          # SQLAlchemy, Migrate, LoginManager, CSRF, Limiter, Talisman
│   ├── cli.py                 # CLI commands (create-owner, seed-demo, generate-rent)
│   ├── models/                # Domain-separated database models
│   │   ├── user.py            # User, TenantProfile
│   │   ├── property.py        # Property, Room, Bed, Amenity, RoomPhoto
│   │   ├── booking.py         # Booking, Allocation, Deposit
│   │   ├── financial.py       # RentCharge, Payment
│   │   ├── operations.py      # Complaint, Notice, TourRequest, Review
│   │   └── settings.py        # SiteSetting, ActivityLog, Notification
│   ├── auth/                  # Authentication blueprint (Login, Register, Password Reset)
│   ├── public/                # Public website blueprint (Home, Rooms, Amenities, Tour, FAQ)
│   ├── owner/                 # Owner admin blueprint (Dashboard, Rooms, Tenants, Rent)
│   ├── tenant/                # Tenant resident portal blueprint
│   ├── api/                   # Read-only JSON API blueprint (/api/rooms)
│   ├── static/                # CSS design system, vanilla JS, images
│   └── templates/             # HTML5 Jinja2 templates (base, public, owner, tenant, errors)
├── migrations/                # Alembic database migrations
├── tests/                     # Automated unit and integration test suite
├── config.py                  # Dev, Testing, and Production configurations
├── run.py                     # Local development entrypoint
├── wsgi.py                    # Production WSGI entrypoint (Waitress/Gunicorn)
├── requirements.txt           # Core Python dependencies
├── requirements-dev.txt       # Development and testing dependencies
└── README.md
```

---

## 📄 License
This project is licensed under the MIT License.
