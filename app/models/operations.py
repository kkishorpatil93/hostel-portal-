"""Operational models: Complaints, notices, tour requests, and tenant reviews."""

from datetime import datetime

from app.extensions import db


class ComplaintCategory:
    MAINTENANCE = "Maintenance"
    PLUMBING = "Plumbing"
    ELECTRICAL = "Electrical"
    WIFI = "Wi-Fi"
    CLEANLINESS = "Cleanliness"
    FOOD = "Food"
    NOISE = "Noise"
    SECURITY = "Security"
    OTHER = "Other"


class ComplaintPriority:
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class ComplaintStatus:
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class NoticeAudience:
    ALL = "all"
    TENANT = "tenant"


class TourStatus:
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Complaint(db.Model):
    """Tenant grievances and maintenance requests."""

    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default=ComplaintCategory.MAINTENANCE, nullable=False)
    priority = db.Column(db.String(20), default=ComplaintPriority.MEDIUM, nullable=False)
    status = db.Column(db.String(30), default=ComplaintStatus.OPEN, nullable=False, index=True)
    owner_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    attachments = db.relationship("ComplaintAttachment", backref="complaint", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Complaint ID {self.id}: {self.title} ({self.status})>"


class ComplaintAttachment(db.Model):
    """Optional image proof attached to a complaint."""

    __tablename__ = "complaint_attachments"

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    storage_key = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ComplaintAttachment {self.filename}>"


class Notice(db.Model):
    """Announcements published by PG owners for tenants and residents."""

    __tablename__ = "notices"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    audience = db.Column(db.String(20), default=NoticeAudience.TENANT, nullable=False)
    pinned = db.Column(db.Boolean, default=False, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    creator = db.relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Notice {self.title} (Pinned: {self.pinned})>"


class TourRequest(db.Model):
    """Room tour and visit inquiries from potential tenants."""

    __tablename__ = "tour_requests"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    preferred_datetime = db.Column(db.DateTime, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default=TourStatus.PENDING, nullable=False)
    owner_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    room = db.relationship("Room", foreign_keys=[room_id])

    def __repr__(self):
        return f"<TourRequest from {self.name} ({self.status})>"


class Review(db.Model):
    """Tenant ratings and testimonials displayed upon owner moderation."""

    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5 stars
    comment = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Review by Tenant {self.tenant_id}: {self.rating} stars (Approved: {self.is_approved})>"
