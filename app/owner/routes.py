import uuid
from datetime import UTC, datetime
from decimal import Decimal

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import func

from app.auth.decorators import owner_required
from app.extensions import db
from app.models.booking import (
    Allocation,
    AllocationStatus,
    Booking,
    BookingStatus,
    Deposit,
    DepositStatus,
)
from app.models.financial import (
    Payment,
    PaymentMethod,
    PaymentStatus,
    RentCharge,
    RentStatus,
)
from app.models.operations import (
    Complaint,
    ComplaintStatus,
    Notice,
    TourRequest,
)
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
    total_rooms = Room.query.filter_by(is_active=True).count()
    total_beds = Bed.query.join(Room).filter(Room.is_active == True, Bed.is_active == True).count()
    occupied_beds = (
        Allocation.query.join(Bed)
        .join(Room)
        .filter(
            Room.is_active == True,
            Allocation.status.in_([AllocationStatus.ACTIVE, AllocationStatus.NOTICE_SERVED]),
        )
        .count()
    )
    vacant_beds = max(0, total_beds - occupied_beds)
    rooms_list = Room.query.filter_by(is_active=True).order_by(Room.room_number).all()

    return render_template(
        "owner/rooms.html",
        rooms=rooms_list,
        total_rooms=total_rooms,
        total_beds=total_beds,
        occupied_beds=occupied_beds,
        vacant_beds=vacant_beds,
        currency_symbol="₹",
    )


@owner_bp.route("/occupancy-report")
@owner_required
def occupancy_report():
    total_rooms = Room.query.filter_by(is_active=True).count()
    total_beds = Bed.query.join(Room).filter(Room.is_active == True, Bed.is_active == True).count()
    occupied_beds = (
        Allocation.query.join(Bed)
        .join(Room)
        .filter(
            Room.is_active == True,
            Allocation.status.in_([AllocationStatus.ACTIVE, AllocationStatus.NOTICE_SERVED]),
        )
        .count()
    )
    vacant_beds = max(0, total_beds - occupied_beds)
    occupancy_pct = round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0.0
    rooms_list = Room.query.filter_by(is_active=True).order_by(Room.room_number).all()

    return render_template(
        "owner/occupancy_report.html",
        rooms=rooms_list,
        total_rooms=total_rooms,
        total_beds=total_beds,
        occupied_beds=occupied_beds,
        vacant_beds=vacant_beds,
        occupancy_pct=occupancy_pct,
        currency_symbol="₹",
    )


@owner_bp.route("/rent-collections")
@owner_required
def rent_collections():
    return rent(default_view="paid")


@owner_bp.route("/pending-payments")
@owner_required
def pending_payments():
    return rent(default_view="pending")


@owner_bp.route("/rent")
@owner_required
def rent(default_view="all"):
    # Sync status for each billing charge
    charges = RentCharge.query.order_by(RentCharge.billing_month.desc(), RentCharge.id.desc()).all()
    for c in charges:
        c.update_status()

    total_invoiced = sum((c.total_due for c in charges), Decimal("0.00"))
    rent_collected = (
        db.session.query(func.coalesce(func.sum(Payment.amount), Decimal("0.00")))
        .filter(Payment.status == PaymentStatus.SUCCESS)
        .scalar()
    ) or Decimal("0.00")
    outstanding_rent = sum((c.outstanding_balance for c in charges), Decimal("0.00"))

    overdue_count = len([c for c in charges if c.status == RentStatus.OVERDUE])
    pending_count = len([c for c in charges if c.outstanding_balance > 0])
    paid_count = len([c for c in charges if c.outstanding_balance == 0])

    recent_payments = Payment.query.order_by(Payment.paid_at.desc()).limit(25).all()
    active_view = request.args.get("view", default_view).lower()

    return render_template(
        "owner/pending_rent.html",
        charges=charges,
        payments=recent_payments,
        total_invoiced=total_invoiced,
        rent_collected=rent_collected,
        outstanding_rent=outstanding_rent,
        overdue_count=overdue_count,
        pending_count=pending_count,
        paid_count=paid_count,
        active_view=active_view,
        currency_symbol="₹",
    )


@owner_bp.route("/rent/<int:charge_id>/pay", methods=["POST"])
@owner_required
def record_payment(charge_id):
    charge = RentCharge.query.get_or_404(charge_id)
    try:
        amount_raw = request.form.get("amount", str(charge.outstanding_balance)).strip()
        amount_val = Decimal(amount_raw)
        if amount_val <= Decimal("0.00"):
            flash("Payment amount must be greater than zero.", "danger")
            return redirect(request.referrer or url_for("owner.rent"))
    except (ValueError, TypeError):
        flash("Invalid payment amount entered.", "danger")
        return redirect(request.referrer or url_for("owner.rent"))

    method = request.form.get("method", PaymentMethod.UPI)
    ref = request.form.get("transaction_reference", "").strip()
    notes = request.form.get("notes", "").strip()

    receipt_number = f"REC-{datetime.now(UTC).strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
    payment = Payment(
        rent_charge_id=charge.id,
        tenant_id=charge.tenant_id,
        amount=amount_val,
        method=method,
        transaction_reference=ref or None,
        receipt_number=receipt_number,
        status=PaymentStatus.SUCCESS,
        recorded_by=current_user.id if current_user.is_authenticated else None,
        notes=notes or f"Offline payment recorded via Owner Portal ({method.upper()})",
    )
    db.session.add(payment)
    charge.update_status()
    db.session.commit()

    flash(
        f"Payment of ₹{amount_val:,.2f} recorded successfully! Receipt #{receipt_number} generated.",
        "success",
    )
    return redirect(request.referrer or url_for("owner.rent"))


@owner_bp.route("/bookings")
@owner_required
def bookings():
    all_bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    total_bookings = len(all_bookings)
    pending_bookings = len([b for b in all_bookings if b.status == BookingStatus.PENDING])
    approved_bookings = len([b for b in all_bookings if b.status == BookingStatus.APPROVED])
    rejected_bookings = len([b for b in all_bookings if b.status == BookingStatus.REJECTED])

    # Preload rooms with beds to allow explicit bed selection
    active_rooms = Room.query.filter_by(is_active=True).order_by(Room.room_number).all()

    return render_template(
        "owner/bookings.html",
        bookings=all_bookings,
        rooms=active_rooms,
        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        approved_bookings=approved_bookings,
        rejected_bookings=rejected_bookings,
        currency_symbol="₹",
    )


@owner_bp.route("/bookings/<int:booking_id>/approve", methods=["POST"])
@owner_required
def approve_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.status == BookingStatus.APPROVED:
        flash(f"Booking #{booking.id} is already approved.", "info")
        return redirect(url_for("owner.bookings"))

    # Check bed availability & prevent double-booking
    bed_id = request.form.get("bed_id", type=int)
    active_allocations_subq = db.session.query(Allocation.bed_id).filter(
        Allocation.status.in_([AllocationStatus.ACTIVE, AllocationStatus.NOTICE_SERVED])
    )

    if bed_id:
        target_bed = Bed.query.filter(
            Bed.id == bed_id,
            Bed.room_id == booking.room_id,
            Bed.is_active == True,
            ~Bed.id.in_(active_allocations_subq),
        ).first()
    else:
        # Find first vacant bed in requested room
        target_bed = Bed.query.filter(
            Bed.room_id == booking.room_id,
            Bed.is_active == True,
            ~Bed.id.in_(active_allocations_subq),
        ).first()

    if not target_bed:
        # DOUBLE-BOOKING PREVENTION
        flash(
            f"Cannot approve booking #{booking.id}: Room {booking.room.room_number} has no vacant beds available! All beds are occupied.",
            "danger",
        )
        return redirect(url_for("owner.bookings"))

    # Allocate bed to applicant
    allocation = Allocation(
        bed_id=target_bed.id,
        tenant_id=booking.tenant_id,
        booking_id=booking.id,
        start_date=booking.requested_move_in_date,
        status=AllocationStatus.ACTIVE,
        monthly_rent_snapshot=booking.room.monthly_rent,
        deposit_amount=booking.room.security_deposit,
    )
    db.session.add(allocation)
    db.session.flush()

    # Create security deposit ledger
    deposit = Deposit(
        allocation_id=allocation.id,
        amount=booking.room.security_deposit,
        status=DepositStatus.HELD,
        notes=f"Deposit registered upon approval of booking #{booking.id}",
    )
    db.session.add(deposit)

    booking.status = BookingStatus.APPROVED
    booking.owner_notes = request.form.get("owner_notes", "Approved by owner")
    db.session.commit()

    flash(
        f"Booking #{booking.id} approved! Bed {target_bed.bed_label} in Room {booking.room.room_number} allocated to {booking.tenant.full_name}.",
        "success",
    )
    return redirect(url_for("owner.bookings"))


@owner_bp.route("/bookings/<int:booking_id>/reject", methods=["POST"])
@owner_required
def reject_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    reason = request.form.get("rejection_reason", "Room unavailable / application declined").strip()
    booking.status = BookingStatus.REJECTED
    booking.rejection_reason = reason
    db.session.commit()

    flash(f"Booking #{booking.id} has been rejected.", "info")
    return redirect(url_for("owner.bookings"))


@owner_bp.route("/complaints")
@owner_required
def complaints():
    complaint_list = Complaint.query.order_by(Complaint.created_at.desc()).all()
    total_complaints = len(complaint_list)
    open_complaints = len([c for c in complaint_list if c.status == ComplaintStatus.OPEN])
    in_progress_complaints = len([c for c in complaint_list if c.status == ComplaintStatus.IN_PROGRESS])
    resolved_complaints = len(
        [c for c in complaint_list if c.status in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]]
    )

    return render_template(
        "owner/complaints.html",
        complaints=complaint_list,
        total_complaints=total_complaints,
        open_complaints=open_complaints,
        in_progress_complaints=in_progress_complaints,
        resolved_complaints=resolved_complaints,
    )


@owner_bp.route("/complaints/<int:complaint_id>/status", methods=["POST"])
@owner_required
def update_complaint_status(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    new_status = request.form.get("status")
    response_notes = request.form.get("owner_response", "").strip()

    valid_statuses = [
        ComplaintStatus.OPEN,
        ComplaintStatus.IN_PROGRESS,
        ComplaintStatus.RESOLVED,
        ComplaintStatus.CLOSED,
    ]
    if new_status in valid_statuses:
        complaint.status = new_status
        if response_notes:
            complaint.owner_response = response_notes
        if new_status in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]:
            complaint.resolved_at = datetime.now(UTC)
        db.session.commit()
        flash(f"Complaint #{complaint.id} status updated to {new_status}.", "success")
    else:
        flash("Invalid complaint status specified.", "danger")

    return redirect(url_for("owner.complaints"))


@owner_bp.route("/tenants")
@owner_required
def tenants():
    all_tenants = User.query.filter_by(role=UserRole.TENANT).all()
    return render_template("owner/tenants.html", tenants=all_tenants)


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

