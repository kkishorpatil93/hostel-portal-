"""Tests for core database models and business logic constraints."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.booking import Allocation, AllocationStatus
from app.models.financial import Payment, PaymentStatus, RentCharge, RentStatus
from app.models.property import Bed, Property, Room
from app.models.settings import ActivityLog
from app.models.user import User, UserRole


def test_user_password_hashing():
    user = User(
        full_name="Pooja Patel",
        email="POOJA@EXAMPLE.COM",  # Lowercase normalization check
        phone="9876543210",
        role=UserRole.TENANT,
    )
    user.set_password("MySecurePass#123")
    db.session.add(user)
    db.session.commit()

    assert user.email == "pooja@example.com"
    assert user.check_password("MySecurePass#123") is True
    assert user.check_password("WrongPassword") is False
    assert user.is_tenant is True
    assert user.is_owner is False


def test_user_failed_login_lockout():
    user = User(
        full_name="Locked User",
        email="locked@example.com",
        phone="9123456789",
    )
    user.set_password("Pass#123")
    db.session.add(user)
    db.session.commit()

    for _ in range(5):
        user.record_failed_login(max_attempts=5, lock_duration_minutes=15)

    assert user.failed_login_count == 5
    assert user.is_locked is True

    user.reset_failed_logins()
    assert user.is_locked is False
    assert user.failed_login_count == 0


def test_unique_email_constraint():
    u1 = User(full_name="User One", email="unique@example.com", phone="9999999991")
    u1.set_password("Pass#123")
    db.session.add(u1)
    db.session.commit()

    u2 = User(full_name="User Two", email="unique@example.com", phone="9999999992")
    u2.set_password("Pass#123")
    db.session.add(u2)

    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_room_and_bed_capacity_tracking():
    prop = Property(
        name="Test PG",
        address="123 Test Road",
        city="Bengaluru",
        state="Karnataka",
        pincode="560001",
        contact_phone="9876543210",
        contact_email="pg@example.com",
    )
    db.session.add(prop)
    db.session.flush()

    room = Room(
        property_id=prop.id,
        room_number="301",
        room_type="Double Sharing",
        floor=3,
        capacity=2,
        monthly_rent=Decimal("12000.00"),
        security_deposit=Decimal("12000.00"),
    )
    db.session.add(room)
    db.session.flush()

    bed1 = Bed(room_id=room.id, bed_label="Bed A")
    bed2 = Bed(room_id=room.id, bed_label="Bed B")
    db.session.add_all([bed1, bed2])
    db.session.commit()

    assert room.total_beds == 2
    assert room.available_beds == 2
    assert bed1.is_occupied is False

    # Allocate bed 1 to a tenant
    tenant = User(full_name="Tenant One", email="t1@example.com", phone="9111111111")
    tenant.set_password("Pass#123")
    db.session.add(tenant)
    db.session.flush()

    alloc = Allocation(
        bed_id=bed1.id,
        tenant_id=tenant.id,
        start_date=date(2026, 10, 1),
        status=AllocationStatus.ACTIVE,
        monthly_rent_snapshot=room.monthly_rent,
        deposit_amount=room.security_deposit,
    )
    db.session.add(alloc)
    db.session.commit()

    assert bed1.is_occupied is True
    assert bed2.is_occupied is False
    assert room.available_beds == 1


def test_rent_charge_calculations_and_status():
    prop = Property(
        name="Billing Test PG",
        address="456 Billing St",
        city="Bengaluru",
        state="Karnataka",
        pincode="560001",
        contact_phone="9876543210",
        contact_email="billing@example.com",
    )
    db.session.add(prop)
    db.session.flush()

    room = Room(
        property_id=prop.id,
        room_number="101",
        room_type="Single",
        monthly_rent=Decimal("15000.00"),
        security_deposit=Decimal("15000.00"),
    )
    db.session.add(room)
    db.session.flush()

    bed = Bed(room_id=room.id, bed_label="Bed 1")
    db.session.add(bed)
    db.session.flush()

    tenant = User(full_name="Billing Tenant", email="bill@example.com", phone="9222222222")
    tenant.set_password("Pass#123")
    db.session.add(tenant)
    db.session.flush()

    alloc = Allocation(
        bed_id=bed.id,
        tenant_id=tenant.id,
        start_date=date(2026, 10, 1),
        status=AllocationStatus.ACTIVE,
        monthly_rent_snapshot=room.monthly_rent,
    )
    db.session.add(alloc)
    db.session.flush()

    charge = RentCharge(
        allocation_id=alloc.id,
        tenant_id=tenant.id,
        billing_month=date(2026, 10, 1),
        amount_due=Decimal("15000.00"),
        late_fee=Decimal("500.00"),
        due_date=date(2026, 10, 5),
        status=RentStatus.PENDING,
    )
    db.session.add(charge)
    db.session.commit()

    assert charge.total_due == Decimal("15500.00")
    assert charge.total_paid == Decimal("0.00")
    assert charge.outstanding_balance == Decimal("15500.00")

    # Record partial payment
    p1 = Payment(
        rent_charge_id=charge.id,
        tenant_id=tenant.id,
        amount=Decimal("5000.00"),
        method="upi",
        receipt_number="REC-TEST-001",
        status=PaymentStatus.SUCCESS,
    )
    db.session.add(p1)
    db.session.commit()

    charge.update_status()
    assert charge.total_paid == Decimal("5000.00")
    assert charge.outstanding_balance == Decimal("10500.00")
    assert charge.status == RentStatus.PARTIAL

    # Record remaining payment
    p2 = Payment(
        rent_charge_id=charge.id,
        tenant_id=tenant.id,
        amount=Decimal("10500.00"),
        method="bank",
        receipt_number="REC-TEST-002",
        status=PaymentStatus.SUCCESS,
    )
    db.session.add(p2)
    db.session.commit()

    charge.update_status()
    assert charge.total_paid == Decimal("15500.00")
    assert charge.outstanding_balance == Decimal("0.00")
    assert charge.status == RentStatus.PAID


def test_activity_log_json():
    log = ActivityLog.log(
        action="TEST_ACTION",
        entity_type="Room",
        entity_id=101,
        details={"room_number": "101", "change": "price_updated"},
        ip_address="127.0.0.1",
    )
    assert log.action == "TEST_ACTION"
    assert log.details["room_number"] == "101"
    assert log.details["change"] == "price_updated"
