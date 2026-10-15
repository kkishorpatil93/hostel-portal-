"""Integration tests for the Owner Portal Dashboard."""

from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models.booking import Booking, BookingStatus
from app.models.financial import Payment, PaymentStatus, RentCharge
from app.models.operations import (
    Complaint,
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
)
from app.models.property import Room
from app.models.user import User


def test_owner_dashboard_unauthorized_redirect(client):
    """Anonymous visitors should be redirected to the login page."""
    response = client.get("/owner/dashboard")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_owner_dashboard_forbidden_for_tenant(client):
    """Authenticated tenants should be prevented from viewing the owner dashboard."""
    # Log in as demo tenant
    login_res = client.post(
        "/auth/login",
        data={"email": "arjun.sharma@example.com", "password": "TenantPass#2026"},
        follow_redirects=True,
    )
    assert login_res.status_code == 200

    response = client.get("/owner/dashboard")
    # Owner-only routes return 404 to avoid leaking admin paths
    assert response.status_code == 404


def test_owner_dashboard_renders_live_metrics(client):
    """Owner dashboard should accurately compute and display occupancy and financial totals."""
    # Log in as seeded demo owner
    login_res = client.post(
        "/auth/login",
        data={"email": "owner@staynest.local", "password": "OwnerSecure#2026"},
        follow_redirects=True,
    )
    assert login_res.status_code == 200

    dash_res = client.get("/owner/dashboard")
    assert dash_res.status_code == 200
    html = dash_res.get_data(as_text=True)

    # Verify calculated figures in HTML
    # Demo seed has 4 active rooms, 8 total beds, 1 occupied bed (Bed A in Room 101), 7 vacant beds (12.5% occupancy)
    assert "Overview & Operations" in html
    assert "Bed Occupancy" in html
    assert "12.5%" in html
    assert "7</strong> vacant beds" in html
    assert "4 rooms" in html
    assert "18,000.00" in html  # Demo rent charge for Room 101


def test_owner_dashboard_with_payments_and_bookings(client):
    """Dashboard metrics should dynamically react when new payments and bookings are added."""
    tenant = User.query.filter_by(email="arjun.sharma@example.com").first()
    room_102 = Room.query.filter_by(room_number="102").first()
    charge = RentCharge.query.first()

    # 1. Add a pending booking request
    booking = Booking(
        tenant_id=tenant.id,
        room_id=room_102.id,
        requested_move_in_date=date(2026, 11, 1),
        status=BookingStatus.PENDING,
    )
    db.session.add(booking)

    # 2. Add a partial payment of ₹6,000.00
    payment = Payment(
        rent_charge_id=charge.id,
        tenant_id=tenant.id,
        amount=Decimal("6000.00"),
        method="upi",
        receipt_number="REC-TEST-DASH-002",
        status=PaymentStatus.SUCCESS,
    )
    db.session.add(payment)

    # 3. Add an open complaint
    complaint = Complaint(
        tenant_id=tenant.id,
        room_id=room_102.id,
        title="High-speed Wi-Fi disconnects frequently",
        description="Speed drops significantly in the evenings.",
        category=ComplaintCategory.WIFI,
        priority=ComplaintPriority.HIGH,
        status=ComplaintStatus.OPEN,
    )
    db.session.add(complaint)
    db.session.commit()

    # Log in as Owner and test GET /owner/dashboard
    client.post(
        "/auth/login",
        data={"email": "owner@staynest.local", "password": "OwnerSecure#2026"},
        follow_redirects=True,
    )

    dash_res = client.get("/owner/dashboard")
    assert dash_res.status_code == 200
    html = dash_res.get_data(as_text=True)

    # Financials: Collected = ₹6,000.00, Outstanding = ₹12,000.00 (18000 - 6000)
    assert "6,000.00" in html
    assert "12,000.00" in html

    # Bookings & Complaints
    assert "Arjun Sharma" in html
    assert "High-speed Wi-Fi disconnects frequently" in html
    assert "Room 102" in html

