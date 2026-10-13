"""Financial models: Rent charges, billing cycles, payments, and receipts."""

from datetime import datetime
from decimal import Decimal

from app.extensions import db


class RentStatus:
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    OVERDUE = "OVERDUE"


class PaymentMethod:
    CASH = "cash"
    UPI = "upi"
    BANK_TRANSFER = "bank"
    ONLINE = "online"


class PaymentStatus:
    SUCCESS = "SUCCESS"
    PENDING = "PENDING"
    FAILED = "FAILED"


class RentCharge(db.Model):
    """Monthly billing line item generated for an active allocation."""

    __tablename__ = "rent_charges"
    __table_args__ = (
        db.UniqueConstraint("allocation_id", "billing_month", name="uq_allocation_billing_month"),
    )

    id = db.Column(db.Integer, primary_key=True)
    allocation_id = db.Column(db.Integer, db.ForeignKey("allocations.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    billing_month = db.Column(db.Date, nullable=False)  # Normalized to 1st of month (e.g. 2026-10-01)
    amount_due = db.Column(db.Numeric(10, 2), nullable=False)
    late_fee = db.Column(db.Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(30), default=RentStatus.PENDING, nullable=False, index=True)
    notes = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    payments = db.relationship("Payment", backref="rent_charge", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def total_due(self) -> Decimal:
        return Decimal(str(self.amount_due)) + Decimal(str(self.late_fee or "0.00"))

    @property
    def total_paid(self) -> Decimal:
        paid_sum = sum(
            (Decimal(str(p.amount)) for p in self.payments.filter_by(status=PaymentStatus.SUCCESS)),
            Decimal("0.00"),
        )
        return paid_sum

    @property
    def outstanding_balance(self) -> Decimal:
        balance = self.total_due - self.total_paid
        return max(Decimal("0.00"), balance)

    def update_status(self) -> None:
        """Sync charge status with payments."""
        paid = self.total_paid
        due = self.total_due
        if paid >= due:
            self.status = RentStatus.PAID
        elif paid > Decimal("0.00"):
            self.status = RentStatus.PARTIAL
        else:
            from datetime import date
            if date.today() > self.due_date:
                self.status = RentStatus.OVERDUE
            else:
                self.status = RentStatus.PENDING

    def __repr__(self):
        return f"<RentCharge ID {self.id}: Alloc {self.allocation_id} Month {self.billing_month} ({self.status})>"


class Payment(db.Model):
    """Payment transaction record against a rent charge."""

    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    rent_charge_id = db.Column(db.Integer, db.ForeignKey("rent_charges.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    paid_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    method = db.Column(db.String(30), default=PaymentMethod.UPI, nullable=False)
    transaction_reference = db.Column(db.String(100), nullable=True)  # UPI UTR or Bank Ref
    status = db.Column(db.String(30), default=PaymentStatus.SUCCESS, nullable=False)
    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    receipt_number = db.Column(db.String(60), unique=True, nullable=False, index=True)
    gateway_order_id = db.Column(db.String(100), nullable=True)
    gateway_payment_id = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    recorder = db.relationship("User", foreign_keys=[recorded_by])

    def __repr__(self):
        return f"<Payment {self.receipt_number}: ₹{self.amount} via {self.method}>"
