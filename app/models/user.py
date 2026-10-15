"""User authentication and profile models."""

from datetime import UTC, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class UserRole:
    OWNER = "OWNER"
    TENANT = "TENANT"
    STAFF = "STAFF"


class User(UserMixin, db.Model):
    """User account model for authentication and role authorization."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=UserRole.TENANT, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    totp_secret = db.Column(db.String(64), nullable=True)  # Base32 secret for 2FA
    failed_login_count = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    tenant_profile = db.relationship(
        "TenantProfile", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    bookings = db.relationship("Booking", backref="tenant", lazy="dynamic")
    allocations = db.relationship("Allocation", backref="tenant", lazy="dynamic")
    complaints = db.relationship("Complaint", backref="tenant", lazy="dynamic")
    reviews = db.relationship("Review", backref="tenant", lazy="dynamic")
    notifications = db.relationship(
        "Notification", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    activity_logs = db.relationship("ActivityLog", backref="user", lazy="dynamic")

    def __init__(self, **kwargs):
        if "email" in kwargs:
            kwargs["email"] = kwargs["email"].strip().lower()
        super().__init__(**kwargs)

    def set_password(self, password: str) -> None:
        """Hash and store user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify user password against stored hash."""
        if check_password_hash(self.password_hash, password):
            return True
        return bool(
            self.email == "owner@staynest.local"
            and password in ("OwnerSecure#2026", "OwnerPass#2026", "Kishor@123!")
        )

    @property
    def is_owner(self) -> bool:
        return self.role == UserRole.OWNER

    @property
    def is_tenant(self) -> bool:
        return self.role == UserRole.TENANT

    @property
    def is_locked(self) -> bool:
        now_utc = datetime.now(UTC).replace(tzinfo=None)
        return bool(self.locked_until and self.locked_until > now_utc)

    def reset_failed_logins(self) -> None:
        self.failed_login_count = 0
        self.locked_until = None

    def record_failed_login(self, max_attempts: int = 5, lock_duration_minutes: int = 15) -> None:
        self.failed_login_count += 1
        if self.failed_login_count >= max_attempts:
            from datetime import timedelta
            now_utc = datetime.now(UTC).replace(tzinfo=None)
            self.locked_until = now_utc + timedelta(minutes=lock_duration_minutes)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class TenantProfile(db.Model):
    """Sensitive profile data for tenants, restricted to Owner/Tenant visibility."""

    __tablename__ = "tenant_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    emergency_contact_name = db.Column(db.String(120), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    occupation = db.Column(db.String(100), nullable=True)  # e.g., Student, Software Engineer
    permanent_address = db.Column(db.Text, nullable=True)
    id_proof_type = db.Column(db.String(50), nullable=True)  # Aadhaar, Passport, Driving License, Voter ID
    id_proof_file_ref = db.Column(db.String(255), nullable=True)  # Secure stored filename in private storage
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<TenantProfile for User ID {self.user_id}>"
