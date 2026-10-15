from decimal import Decimal

from flask import render_template
from sqlalchemy import func

from app.auth.decorators import owner_required
from app.extensions import db
from app.models.booking import Allocation, AllocationStatus, Booking, BookingStatus
from app.models.financial import Payment, PaymentStatus, RentCharge
from app.models.operations import Complaint, ComplaintStatus, Notice, TourRequest
from app.models.property import Bed, Property, Room
from app.models.user import User, UserRole
from app.owner import owner_bp


@owner_bp.route("/dashboard")
@owner_required
def dashboard():
    total_rooms = Room.query.filter_by(is_active=True).count()
    total_beds = Bed.query.filter_by(is_active=True).count()
    occupied_beds = Allocation.query.filter_by(status=AllocationStatus.ACTIVE).count()
    vacant_beds = max(0, total_beds - occupied_beds)
    occupancy_pct = round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0.0

    pending_bookings = Booking.query.filter_by(status=BookingStatus.PENDING).count()
    pending_tours = TourRequest.query.filter_by(status="PENDING").count()
    open_complaints = Complaint.query.filter(
        Complaint.status.in_([ComplaintStatus.OPEN, ComplaintStatus.IN_PROGRESS])
    ).count()

    # Calculate real financial metrics from live payments and rent charges
    rent_collected = (
        db.session.query(func.coalesce(func.sum(Payment.amount), Decimal("0.00")))
        .filter(Payment.status == PaymentStatus.SUCCESS)
        .scalar()
    ) or Decimal("0.00")

    all_charges = RentCharge.query.all()
    outstanding_rent = sum((c.outstanding_balance for c in all_charges), Decimal("0.00"))

    # Recent activity items
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    recent_complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(5).all()
    rooms_summary = Room.query.filter_by(is_active=True).order_by(Room.room_number).all()

    return render_template(
        "owner/dashboard.html",
        total_rooms=total_rooms,
        total_beds=total_beds,
        occupied_beds=occupied_beds,
        available_beds=vacant_beds,
        vacant_beds=vacant_beds,
        occupancy_pct=occupancy_pct,
        pending_bookings=pending_bookings,
        pending_tours=pending_tours,
        open_complaints=open_complaints,
        rent_collected=rent_collected,
        outstanding_rent=outstanding_rent,
        recent_bookings=recent_bookings,
        recent_complaints=recent_complaints,
        rooms_summary=rooms_summary,
        currency_symbol="₹",
    )


@owner_bp.route("/rooms")
@owner_required
def rooms():
    rooms_list = Room.query.all()
    return render_template("owner/rooms.html", rooms=rooms_list)


@owner_bp.route("/bookings")
@owner_required
def bookings():
    all_bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template("owner/bookings.html", bookings=all_bookings)


@owner_bp.route("/tenants")
@owner_required
def tenants():
    all_tenants = User.query.filter_by(role=UserRole.TENANT).all()
    return render_template("owner/tenants.html", tenants=all_tenants)


@owner_bp.route("/rent")
@owner_required
def rent():
    charges = RentCharge.query.order_by(RentCharge.billing_month.desc()).all()
    return render_template("owner/rent.html", charges=charges)


@owner_bp.route("/complaints")
@owner_required
def complaints():
    complaint_list = Complaint.query.order_by(Complaint.created_at.desc()).all()
    return render_template("owner/complaints.html", complaints=complaint_list)


@owner_bp.route("/notices")
@owner_required
def notices():
    notice_list = Notice.query.order_by(Notice.created_at.desc()).all()
    return render_template("owner/notices.html", notices=notice_list)


@owner_bp.route("/settings")
@owner_required
def settings():
    prop = Property.query.first()
    return render_template("owner/settings.html", property=prop)
