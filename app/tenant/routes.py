"""Tenant portal routes."""

from flask import render_template
from flask_login import current_user

from app.auth.decorators import tenant_required
from app.models.booking import Allocation, AllocationStatus, Booking
from app.models.financial import RentCharge
from app.models.operations import Complaint, Notice
from app.tenant import tenant_bp


@tenant_bp.route("/dashboard")
@tenant_required
def dashboard():
    active_allocation = (
        Allocation.query.filter_by(tenant_id=current_user.id, status=AllocationStatus.ACTIVE)
        .first()
    )
    my_bookings = (
        Booking.query.filter_by(tenant_id=current_user.id)
        .order_by(Booking.created_at.desc())
        .limit(3)
        .all()
    )
    pending_charges = (
        RentCharge.query.filter_by(tenant_id=current_user.id)
        .filter(RentCharge.status != "PAID")
        .all()
    )
    my_complaints = (
        Complaint.query.filter_by(tenant_id=current_user.id)
        .order_by(Complaint.created_at.desc())
        .limit(3)
        .all()
    )
    recent_notices = Notice.query.order_by(Notice.pinned.desc(), Notice.created_at.desc()).limit(3).all()

    return render_template(
        "tenant/dashboard.html",
        allocation=active_allocation,
        bookings=my_bookings,
        pending_charges=pending_charges,
        complaints=my_complaints,
        notices=recent_notices,
    )


@tenant_bp.route("/profile")
@tenant_required
def profile():
    return render_template("tenant/profile.html", user=current_user)


@tenant_bp.route("/bookings")
@tenant_required
def bookings():
    bookings_list = (
        Booking.query.filter_by(tenant_id=current_user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    return render_template("tenant/bookings.html", bookings=bookings_list)


@tenant_bp.route("/payments")
@tenant_required
def payments():
    charges = (
        RentCharge.query.filter_by(tenant_id=current_user.id)
        .order_by(RentCharge.billing_month.desc())
        .all()
    )
    return render_template("tenant/payments.html", charges=charges)


@tenant_bp.route("/complaints")
@tenant_required
def complaints():
    my_complaints = (
        Complaint.query.filter_by(tenant_id=current_user.id)
        .order_by(Complaint.created_at.desc())
        .all()
    )
    return render_template("tenant/complaints.html", complaints=my_complaints)


@tenant_bp.route("/notices")
@tenant_required
def notices():
    all_notices = Notice.query.order_by(Notice.pinned.desc(), Notice.created_at.desc()).all()
    return render_template("tenant/notices.html", notices=all_notices)
