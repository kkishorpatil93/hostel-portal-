"""Property, Room, Bed, Amenity, and Media models."""

from datetime import datetime

from app.extensions import db

# Many-to-many association table between rooms and amenities
room_amenities = db.Table(
    "room_amenities",
    db.Column("room_id", db.Integer, db.ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True),
    db.Column("amenity_id", db.Integer, db.ForeignKey("amenities.id", ondelete="CASCADE"), primary_key=True),
)


class Amenity(db.Model):
    """PG and Room amenities (e.g. High-speed Wi-Fi, AC, Attached Washroom, Power Backup)."""

    __tablename__ = "amenities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    icon_name = db.Column(db.String(50), nullable=False, default="check-circle")  # SVG or icon name
    category = db.Column(db.String(50), default="general")  # e.g., room, common, food, security
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Amenity {self.name}>"


class Property(db.Model):
    """Top-level PG property/building model."""

    __tablename__ = "properties"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False, default="Bengaluru")
    state = db.Column(db.String(100), nullable=False, default="Karnataka")
    pincode = db.Column(db.String(20), nullable=False, default="560001")
    description = db.Column(db.Text, nullable=True)
    contact_phone = db.Column(db.String(20), nullable=False)
    contact_email = db.Column(db.String(120), nullable=False)
    map_embed_url = db.Column(db.Text, nullable=True)
    check_in_time = db.Column(db.String(20), default="10:00 AM")
    check_out_time = db.Column(db.String(20), default="12:00 PM")
    rules = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    rooms = db.relationship("Room", backref="property", lazy="dynamic", cascade="all, delete-orphan")
    notices = db.relationship("Notice", backref="property", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Property {self.name}>"


class Room(db.Model):
    """Room within a property, containing individual beds."""

    __tablename__ = "rooms"
    __table_args__ = (
        db.UniqueConstraint("property_id", "room_number", name="uq_property_room_number"),
    )

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    room_number = db.Column(db.String(50), nullable=False)  # e.g. "101", "204-A"
    room_type = db.Column(db.String(50), nullable=False)  # Single, Double Sharing, Triple Sharing, Four Sharing
    floor = db.Column(db.Integer, default=1, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=1)  # Maximum number of beds
    monthly_rent = db.Column(db.Numeric(10, 2), nullable=False)  # Base rent per bed
    security_deposit = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Soft-delete flag
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    beds = db.relationship("Bed", backref="room", lazy="dynamic", cascade="all, delete-orphan")
    photos = db.relationship("RoomPhoto", backref="room", lazy="dynamic", cascade="all, delete-orphan")
    amenities = db.relationship("Amenity", secondary=room_amenities, backref="rooms", lazy="subquery")
    bookings = db.relationship("Booking", backref="room", lazy="dynamic")
    complaints = db.relationship("Complaint", backref="room", lazy="dynamic")

    @property
    def total_beds(self) -> int:
        return self.beds.filter_by(is_active=True).count()

    @property
    def available_beds(self) -> int:
        from sqlalchemy import select

        from app.models.booking import Allocation, AllocationStatus
        allocated_bed_ids = (
            select(Allocation.bed_id)
            .filter(Allocation.status.in_([AllocationStatus.ACTIVE, AllocationStatus.NOTICE_SERVED]))
        )
        return (
            self.beds.filter(
                Bed.is_active == True,
                ~Bed.id.in_(allocated_bed_ids)
            ).count()
        )

    def __repr__(self):
        return f"<Room {self.room_number} ({self.room_type})>"


class Bed(db.Model):
    """Specific bed unit in a room. Source of truth for occupancy."""

    __tablename__ = "beds"
    __table_args__ = (
        db.UniqueConstraint("room_id", "bed_label", name="uq_room_bed_label"),
    )

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    bed_label = db.Column(db.String(50), nullable=False)  # e.g. "Bed 1", "Bed A", "Window Bed"
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    allocations = db.relationship("Allocation", backref="bed", lazy="dynamic")

    @property
    def is_occupied(self) -> bool:
        from app.models.booking import Allocation, AllocationStatus
        return (
            self.allocations.filter(
                Allocation.status.in_([AllocationStatus.ACTIVE, AllocationStatus.NOTICE_SERVED])
            ).first()
            is not None
        )

    def __repr__(self):
        return f"<Bed {self.bed_label} in Room ID {self.room_id}>"


class RoomPhoto(db.Model):
    """Public photo gallery for rooms."""

    __tablename__ = "room_photos"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    storage_key = db.Column(db.String(255), nullable=False)  # File path or storage ID
    alt_text = db.Column(db.String(150), nullable=True)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<RoomPhoto {self.storage_key}>"
