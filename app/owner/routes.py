"""Owner admin portal views."""

from flask import render_template

from app.auth.decorators import owner_required
from app.models.booking import Allocation, AllocationStatus, Booking, BookingStatus
from app.models.financial import RentCharge
from app.models.operations import Complaint, ComplaintStatus, Notice, TourRequest
from app.models.property import Bed, Property, Room
from app.models.user import User, UserRole
from app.owner import owner_bp


@owner_bp.route("/dashboard")
@owner_required
def dashboard():
    total_rooms = Room.query.filter_by(is_active=True).count()
    total_beds = Bed.query.filter_by(is_active=True).count()
    active_allocations = Allocation.query.filter_by(status=AllocationStatus.ACTIVE).count()
    available_beds = max(0, total_beds - active_allocations)
    occupancy_pct = round((active_allocations / total_beds * 100), 1) if total_beds > 0 else 0

    pending_bookings = Booking.query.filter_by(status=BookingStatus.PENDING).count()
    pending_tours = TourRequest.query.filter_by(status="PENDING").count()
    open_complaints = Complaint.query.filter(Complaint.status.in_([ComplaintStatus.OPEN, ComplaintStatus.IN_PROGRESS])).count()

    return render_template(
        "owner/dashboard.html",
        total_rooms=total_rooms,
        total_beds=total_beds,
        occupied_beds=active_allocations,
        available_beds=available_beds,
        occupancy_pct=occupancy_pct,
        pending_bookings=pending_bookings,
        pending_tours=pending_tours,
        open_complaints=open_complaints,
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
