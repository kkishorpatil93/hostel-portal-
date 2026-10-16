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


def test_owner_dashboard_unauthenticated_redirects_to_login(client):
    """Unauthenticated access to Owner dashboard must redirect to login."""
    response = client.get("/owner/dashboard")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_owner_dashboard_forbidden_for_tenant(authenticated_tenant_client):
    """Authenticated tenant must receive 403 Forbidden when attempting to access owner dashboard."""
    response = authenticated_tenant_client.get("/owner/dashboard")
    assert response.status_code == 403


def test_auth_login_renders_login_form(client):
    """Accessing /auth/login while logged out renders the sign in form."""
    response = client.get("/auth/login")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Sign In" in html
    assert 'name="email"' in html
    assert 'name="password"' in html


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


def test_owner_dashboard_summary_cards_are_clickable(authenticated_owner_client):
    """Every summary KPI card on the dashboard must be clickable and link to its details page."""
    res = authenticated_owner_client.get("/owner/dashboard")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # 1. Bed Occupancy -> /owner/rooms
    assert 'href="/owner/rooms"' in html
    # 2. Occupancy Rate -> /owner/occupancy-report
    assert 'href="/owner/occupancy-report"' in html
    # 3. Rent Collected -> /owner/rent-collections
    assert 'href="/owner/rent-collections"' in html
    # 4. Outstanding Rent -> /owner/pending-payments
    assert 'href="/owner/pending-payments"' in html
    # 5. Pending Bookings -> /owner/bookings
    assert 'href="/owner/bookings"' in html
    # 6. Open Complaints -> /owner/complaints
    assert 'href="/owner/complaints"' in html


def test_rooms_and_beds_details_page(authenticated_owner_client):
    """Rooms & Beds details page should display room number, sharing type, beds, tenant info, and filters."""
    res = authenticated_owner_client.get("/owner/rooms")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # Navigation & Title
    assert "Rooms & Beds Details" in html
    assert "Back to Dashboard" in html
    assert 'href="/owner/dashboard"' in html

    # Top summary metrics consistent with dashboard (4 rooms, 8 beds, 1 occupied, 7 vacant)
    assert "Total Active Rooms" in html
    assert "Total Bed Capacity" in html
    assert "Occupied Beds" in html
    assert "Vacant Beds" in html

    # Room items & sharing types
    assert "Room 101" in html
    assert "Single Private Room" in html
    assert "Room 102" in html
    assert "Double Sharing Room" in html

    # Tenant Details on Bed A in Room 101
    assert "Arjun Sharma (Demo Tenant)" in html
    assert "9876511111" in html
    assert "arjun.sharma@example.com" in html

    # Vacant bed indicator
    assert "Ready for new booking" in html

    # Search & status filter toolbar
    assert "room-search-input" in html
    assert "All Rooms" in html
    assert "Vacant" in html
    assert "Partially Occupied" in html
    assert "Fully Occupied" in html


def test_complaints_details_page_and_status_update(authenticated_owner_client):
    """Complaints page should render tickets and allow updating ticket status with notes."""
    tenant = User.query.filter_by(email="arjun.sharma@example.com").first()
    room_101 = Room.query.filter_by(room_number="101").first()

    complaint = Complaint(
        tenant_id=tenant.id,
        room_id=room_101.id,
        title="AC remote control not working",
        description="Batteries replaced but display remains blank.",
        category=ComplaintCategory.ELECTRICAL,
        priority=ComplaintPriority.HIGH,
        status=ComplaintStatus.OPEN,
    )
    db.session.add(complaint)
    db.session.commit()

    # GET /owner/complaints
    res = authenticated_owner_client.get("/owner/complaints")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Maintenance" in html
    assert "AC remote control not working" in html
    assert "Arjun Sharma" in html
    assert "Room 101" in html
    assert "High" in html

    # POST /owner/complaints/<id>/status
    post_res = authenticated_owner_client.post(
        f"/owner/complaints/{complaint.id}/status",
        data={"status": "IN_PROGRESS", "owner_response": "Technician scheduled for 4 PM"},
        follow_redirects=True,
    )
    assert post_res.status_code == 200
    updated_html = post_res.get_data(as_text=True)
    assert "In Progress" in updated_html
    assert "Technician scheduled for 4 PM" in updated_html

    # Check database
    updated_complaint = Complaint.query.get(complaint.id)
    assert updated_complaint.status == ComplaintStatus.IN_PROGRESS
    assert updated_complaint.owner_response == "Technician scheduled for 4 PM"


def test_bookings_details_page_approve_and_double_booking_prevention(authenticated_owner_client):
    """Approving a booking allocates a bed, and prevents double-booking if no beds are vacant."""
    tenant = User.query.filter_by(email="arjun.sharma@example.com").first()
    room_101 = Room.query.filter_by(room_number="101").first()
    room_102 = Room.query.filter_by(room_number="102").first()

    # Room 101 already has Bed A occupied in demo seed. Capacity is 1 bed, so it has 0 vacant beds!
    booking_full_room = Booking(
        tenant_id=tenant.id,
        room_id=room_101.id,
        requested_move_in_date=date(2026, 11, 1),
        status=BookingStatus.PENDING,
    )
    # Room 102 has 2 beds, both vacant.
    booking_vacant_room = Booking(
        tenant_id=tenant.id,
        room_id=room_102.id,
        requested_move_in_date=date(2026, 11, 5),
        status=BookingStatus.PENDING,
    )
    db.session.add_all([booking_full_room, booking_vacant_room])
    db.session.commit()

    # GET /owner/bookings
    res = authenticated_owner_client.get("/owner/bookings")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Booking Requests" in html
    assert "Room 101" in html
    assert "Room 102" in html

    # 1. Test Double-Booking Prevention: Attempt to approve booking for Room 101 (0 vacant beds)
    res_full = authenticated_owner_client.post(
        f"/owner/bookings/{booking_full_room.id}/approve",
        data={},
        follow_redirects=True,
    )
    assert res_full.status_code == 200
    html_full = res_full.get_data(as_text=True)
    assert "has no vacant beds available" in html_full
    assert Booking.query.get(booking_full_room.id).status == BookingStatus.PENDING

    # 2. Test Successful Approval: Approve booking for Room 102 (vacant beds available)
    res_vacant = authenticated_owner_client.post(
        f"/owner/bookings/{booking_vacant_room.id}/approve",
        data={"owner_notes": "Welcome to StayNest"},
        follow_redirects=True,
    )
    assert res_vacant.status_code == 200
    html_vacant = res_vacant.get_data(as_text=True)
    assert "approved" in html_vacant.lower()
    approved_booking = Booking.query.get(booking_vacant_room.id)
    assert approved_booking.status == BookingStatus.APPROVED
    assert approved_booking.allocation is not None


def test_bookings_details_page_reject(authenticated_owner_client):
    """Owner can decline or reject a booking with a rejection reason."""
    tenant = User.query.filter_by(email="arjun.sharma@example.com").first()
    room_102 = Room.query.filter_by(room_number="102").first()

    booking = Booking(
        tenant_id=tenant.id,
        room_id=room_102.id,
        requested_move_in_date=date(2026, 12, 1),
        status=BookingStatus.PENDING,
    )
    db.session.add(booking)
    db.session.commit()

    res = authenticated_owner_client.post(
        f"/owner/bookings/{booking.id}/reject",
        data={"rejection_reason": "Requested dates conflict with maintenance schedule"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "rejected" in res.get_data(as_text=True).lower()
    updated_b = Booking.query.get(booking.id)
    assert updated_b.status == BookingStatus.REJECTED
    assert updated_b.rejection_reason == "Requested dates conflict with maintenance schedule"


def test_pending_rent_details_page_and_record_payment(authenticated_owner_client):
    """Pending rent page should calculate remaining balance and allow recording offline payments."""
    charge = RentCharge.query.first()
    initial_outstanding = charge.outstanding_balance

    # GET /owner/pending-payments and /owner/rent
    res = authenticated_owner_client.get("/owner/pending-payments")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Rent Accounts" in html
    assert "Record Payment" in html
    assert "Remaining Balance" in html

    # Record a partial payment of ₹5,000.00
    pay_res = authenticated_owner_client.post(
        f"/owner/rent/{charge.id}/pay",
        data={
            "amount": "5000.00",
            "method": "upi",
            "transaction_reference": "UPI-TEST-12345",
            "notes": "Paid via Google Pay",
        },
        follow_redirects=True,
    )
    assert pay_res.status_code == 200
    html_after = pay_res.get_data(as_text=True)
    assert "recorded successfully" in html_after.lower()
    assert "REC-" in html_after

    # Verify charge updated in DB
    db.session.refresh(charge)
    assert charge.outstanding_balance == initial_outstanding - Decimal("5000.00")
    assert charge.total_paid == Decimal("5000.00")
    assert charge.status == "PARTIAL"


def test_occupancy_report_details_page(authenticated_owner_client):
    """Occupancy report page should render formula, overall occupancy %, and room-wise breakdown."""
    res = authenticated_owner_client.get("/owner/occupancy-report")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    assert "Occupancy Report" in html
    assert "Occupancy Rate Benchmark" in html
    assert "(Occupied Beds / Total Beds)" in html
    assert "Room-Wise Occupancy Breakdown" in html
    assert "Room 101" in html
    assert "Room 102" in html
    assert "Room 201" in html
    assert "Room 202" in html
    assert "Total Active Rooms" in html
    assert "Total Bed Capacity" in html
    assert "Occupied Beds" in html
    assert "Vacant Beds" in html



