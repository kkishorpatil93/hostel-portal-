"""Booking requests, bed allocations, and security deposits."""

from datetime import datetime

from app.extensions import db


class BookingStatus:
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class AllocationStatus:
    ACTIVE = "ACTIVE"
    NOTICE_SERVED = "NOTICE_SERVED"
    CHECKED_OUT = "CHECKED_OUT"


class DepositStatus:
    HELD = "HELD"
    DEDUCTED = "DEDUCTED"
    REFUNDED = "REFUNDED"


class Booking(db.Model):
    """Booking requests submitted by visitors or registered tenants."""

    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    requested_move_in_date = db.Column(db.Date, nullable=False)
    duration_months = db.Column(db.Integer, nullable=True)  # e.g., 6 months, 12 months
    status = db.Column(db.String(30), default=BookingStatus.PENDING, nullable=False, index=True)
    notes = db.Column(db.Text, nullable=True)  # Tenant notes or preferences
    owner_notes = db.Column(db.Text, nullable=True)
    rejection_reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    allocation = db.relationship("Allocation", backref="booking", uselist=False)

    def __repr__(self):
        return f"<Booking ID {self.id} (Status: {self.status})>"


class Allocation(db.Model):
    """Active or historical occupancy allocation of a bed to a tenant."""

    __tablename__ = "allocations"

    id = db.Column(db.Integer, primary_key=True)
    bed_id = db.Column(db.Integer, db.ForeignKey("beds.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)  # Check-out date if ended or scheduled
    notice_date = db.Column(db.Date, nullable=True)  # Date notice was submitted
    status = db.Column(db.String(30), default=AllocationStatus.ACTIVE, nullable=False, index=True)
    monthly_rent_snapshot = db.Column(db.Numeric(10, 2), nullable=False)  # Frozen agreed rent rate
    deposit_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    deposit = db.relationship("Deposit", backref="allocation", uselist=False, cascade="all, delete-orphan")
    rent_charges = db.relationship("RentCharge", backref="allocation", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Allocation ID {self.id}: Bed {self.bed_id} -> Tenant {self.tenant_id} ({self.status})>"


class Deposit(db.Model):
    """Security deposit ledger linked to an allocation."""

    __tablename__ = "deposits"

    id = db.Column(db.Integer, primary_key=True)
    allocation_id = db.Column(
        db.Integer, db.ForeignKey("allocations.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    received_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(30), default=DepositStatus.HELD, nullable=False)
    deductions = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    refunded_amount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    refunded_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Deposit for Allocation ID {self.allocation_id}: ₹{self.amount} ({self.status})>"
