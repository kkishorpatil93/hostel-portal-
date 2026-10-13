"""Command line interface (CLI) commands and data seeding for StayNest PG platform."""

import os
from datetime import date, datetime
from decimal import Decimal

import click

from app.extensions import db
from app.models.booking import Allocation, AllocationStatus, Deposit, DepositStatus
from app.models.financial import RentCharge, RentStatus
from app.models.operations import Notice, Review
from app.models.property import Amenity, Bed, Property, Room
from app.models.settings import ActivityLog, SiteSetting
from app.models.user import TenantProfile, User, UserRole


def seed_demo_data(app):
    """Programmatically seed realistic demo data for testing or preview deployments."""
    # 1. Site Settings
    SiteSetting.set_value("site_title", "StayNest Luxury PG for Gents & Ladies")
    SiteSetting.set_value("contact_phone", "+91 98765 43210")
    SiteSetting.set_value("contact_email", "staynestpg@example.com")
    SiteSetting.set_value("address", "12, 4th Cross, Koramangala 5th Block, Bengaluru, Karnataka 560095")

    # 2. Demo Owner
    owner_email = "owner@staynest.local"
    owner = User.query.filter_by(email=owner_email).first()
    if not owner:
        owner = User(
            full_name="Rajesh Sharma (Demo Owner)",
            email=owner_email,
            phone="9876543210",
            role=UserRole.OWNER,
            is_active=True,
            email_verified=True,
        )
        owner.set_password("OwnerSecure#2026")
        db.session.add(owner)
        db.session.commit()

    # 3. Property
    prop = Property.query.first()
    if not prop:
        prop = Property(
            name="StayNest PG Koramangala",
            address="12, 4th Cross, Koramangala 5th Block",
            city="Bengaluru",
            state="Karnataka",
            pincode="560095",
            description="Modern, hygienic, and fully furnished executive PG with premium amenities, high-speed Wi-Fi, 3-time nutritious meals, and 24/7 power backup.",
            contact_phone="+91 98765 43210",
            contact_email="staynestpg@example.com",
            map_embed_url="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3888.752352220556!2d77.62002367507559!3d12.92364028738734!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3bae1450a8b98e1f%3A0x6b42b7811f53d26!2sKoramangala%2C%20Bengaluru%2C%20Karnataka!5e0!3m2!1sen!2sin!4v1700000000000!5m2!1sen!2sin",
            check_in_time="10:00 AM",
            check_out_time="12:00 PM",
            rules="No smoking indoors. Visitors allowed in the lounge until 9 PM. Gate locks at 11 PM.",
        )
        db.session.add(prop)
        db.session.commit()

    # 4. Amenities
    amenities_data = [
        ("High-speed Wi-Fi (300 Mbps)", "wifi", "room", "Fiber internet with uninterrupted connectivity for WFH."),
        ("Air Conditioning (AC)", "wind", "room", "Inverter AC with remote temperature control in all premium rooms."),
        ("Attached Washroom", "bath", "room", "Western sanitary ware with 24/7 hot water geyser."),
        ("3-Time Homely Meals", "utensils", "food", "Hygienic North & South Indian breakfast, lunch, and dinner."),
        ("24/7 Power Backup", "bolt", "general", "Commercial generator ensuring 100% electricity uptime."),
        ("RO Purified Drinking Water", "tint", "general", "Multi-stage RO + UV water dispensing station on each floor."),
        ("Automatic Washing Machines", "washer", "general", "Fully automatic laundry machines and drying zone."),
        ("Biometric & CCTV Security", "shield-alt", "security", "Round-the-clock HD CCTV surveillance and keyless entry."),
    ]
    amenity_objs = []
    for name, icon, cat, desc in amenities_data:
        am = Amenity.query.filter_by(name=name).first()
        if not am:
            am = Amenity(name=name, icon_name=icon, category=cat, description=desc)
            db.session.add(am)
        amenity_objs.append(am)
    db.session.commit()

    # 5. Rooms & Beds
    rooms_specs = [
        ("101", "Single Private Room", 1, 1, Decimal("18000.00"), Decimal("18000.00"), "Spacious private bedroom with dedicated study workstation and balcony."),
        ("102", "Double Sharing Room", 1, 2, Decimal("11000.00"), Decimal("11000.00"), "Comfortable double sharing room with individual wardrobes and side tables."),
        ("201", "Triple Sharing Room", 2, 3, Decimal("8500.00"), Decimal("8500.00"), "Cost-effective triple sharing room with ample natural ventilation and lockers."),
        ("202", "Double Sharing Premium AC", 2, 2, Decimal("13500.00"), Decimal("13500.00"), "Air-conditioned double sharing room with attached western bathroom."),
    ]

    for r_num, r_type, fl, cap, rent, dep, desc in rooms_specs:
        room = Room.query.filter_by(property_id=prop.id, room_number=r_num).first()
        if not room:
            room = Room(
                property_id=prop.id,
                room_number=r_num,
                room_type=r_type,
                floor=fl,
                capacity=cap,
                monthly_rent=rent,
                security_deposit=dep,
                description=desc,
            )
            room.amenities = amenity_objs[:5]
            db.session.add(room)
            db.session.flush()

            for b_idx in range(1, cap + 1):
                bed = Bed(room_id=room.id, bed_label=f"Bed {chr(64 + b_idx)}")
                db.session.add(bed)
    db.session.commit()

    # 6. Demo Tenants
    tenant1_email = "arjun.sharma@example.com"
    t1 = User.query.filter_by(email=tenant1_email).first()
    if not t1:
        t1 = User(
            full_name="Arjun Sharma (Demo Tenant)",
            email=tenant1_email,
            phone="9876511111",
            role=UserRole.TENANT,
            is_active=True,
            email_verified=True,
        )
        t1.set_password("TenantPass#2026")
        db.session.add(t1)
        db.session.flush()

        t1_profile = TenantProfile(
            user_id=t1.id,
            emergency_contact_name="Ramesh Sharma",
            emergency_contact_phone="9876522222",
            occupation="Software Engineer at Tech Mahindra",
            permanent_address="Flat 204, Green Heights, Pune, Maharashtra",
            id_proof_type="Aadhaar",
        )
        db.session.add(t1_profile)

        r101 = Room.query.filter_by(room_number="101").first()
        bed_a = r101.beds.first()
        alloc1 = Allocation(
            bed_id=bed_a.id,
            tenant_id=t1.id,
            start_date=date(2026, 9, 1),
            status=AllocationStatus.ACTIVE,
            monthly_rent_snapshot=r101.monthly_rent,
            deposit_amount=r101.security_deposit,
        )
        db.session.add(alloc1)
        db.session.flush()

        dep1 = Deposit(
            allocation_id=alloc1.id,
            amount=r101.security_deposit,
            status=DepositStatus.HELD,
            notes="Paid via UPI at check-in.",
        )
        db.session.add(dep1)

        rent_chg = RentCharge(
            allocation_id=alloc1.id,
            tenant_id=t1.id,
            billing_month=date(2026, 10, 1),
            amount_due=r101.monthly_rent,
            due_date=date(2026, 10, 5),
            status=RentStatus.PENDING,
        )
        db.session.add(rent_chg)
        db.session.commit()

    # 7. Notices & Reviews
    if Notice.query.count() == 0:
        notice1 = Notice(
            property_id=prop.id,
            title="Diwali Festivities & Special Dinner",
            message="Join us on the terrace this Saturday at 7:30 PM for celebration, sweets, and special dinner!",
            audience="tenant",
            pinned=True,
            created_by=owner.id,
        )
        notice2 = Notice(
            property_id=prop.id,
            title="Wi-Fi Maintenance Notice",
            message="Routine router firmware upgrade scheduled for Sunday between 2:00 AM and 4:00 AM.",
            audience="tenant",
            pinned=False,
            created_by=owner.id,
        )
        db.session.add_all([notice1, notice2])

    if Review.query.count() == 0 and t1:
        rev = Review(
            tenant_id=t1.id,
            rating=5,
            comment="StayNest Koramangala is hands down the cleanest and best managed PG I have stayed at in Bangalore. The food is homely and management is prompt!",
            is_approved=True,
        )
        db.session.add(rev)

    db.session.commit()
    return True


def register_cli_commands(app):
    """Register custom Click commands with the Flask application."""

    @app.cli.command("create-owner")
    @click.option("--name", prompt="Owner Full Name", help="Full legal name of the owner.")
    @click.option("--email", prompt="Owner Email Address", help="Login email.")
    @click.option("--phone", prompt="Owner Mobile Phone", help="10-digit mobile number.")
    @click.password_option(prompt="Owner Password", confirmation_prompt=True, help="Strong password.")
    def create_owner(name, email, phone, password):
        """Securely create the initial PG Owner account."""
        email = email.strip().lower()
        existing = User.query.filter_by(email=email).first()
        if existing:
            click.secho(f"Error: User with email '{email}' already exists.", fg="red", err=True)
            return

        if len(password) < 8:
            click.secho("Error: Password must be at least 8 characters long.", fg="red", err=True)
            return

        owner = User(
            full_name=name.strip(),
            email=email,
            phone=phone.strip(),
            role=UserRole.OWNER,
            is_active=True,
            email_verified=True,
        )
        owner.set_password(password)
        db.session.add(owner)
        db.session.commit()

        # Log creation
        ActivityLog.log(
            action="OWNER_ACCOUNT_CREATED",
            entity_type="User",
            entity_id=owner.id,
            user_id=owner.id,
            details={"email": email, "name": name},
        )
        click.secho(f"Success: Owner account '{email}' created successfully!", fg="green")

    @app.cli.command("seed-demo")
    def seed_demo():
        """Seed realistic, safe sample data for local development and testing only."""
        if (app.config.get("ENV") == "production" or os.getenv("FLASK_ENV") == "production") and not (
            os.getenv("VERCEL") or "VERCEL" in os.environ
        ):
            click.secho("Refusing to seed demo data in production environment.", fg="red", err=True)
            return

        click.echo("Seeding development demo data...")
        seed_demo_data(app)
        click.secho("Demo seed completed successfully!", fg="green")

    @app.cli.command("generate-rent")
    @click.option("--month", default=None, help="Billing month in YYYY-MM format. Defaults to current month.")
    def generate_rent(month):
        """Generate idempotent monthly rent charges for all active allocations."""
        if month:
            try:
                dt = datetime.strptime(month, "%Y-%m")
                billing_date = date(dt.year, dt.month, 1)
            except ValueError:
                click.secho("Invalid month format. Please use YYYY-MM.", fg="red", err=True)
                return
        else:
            today = date.today()
            billing_date = date(today.year, today.month, 1)

        active_allocations = Allocation.query.filter_by(status=AllocationStatus.ACTIVE).all()
        created_count = 0
        skipped_count = 0
        due_day = app.config.get("DEFAULT_RENT_DUE_DAY", 5)

        for alloc in active_allocations:
            existing = RentCharge.query.filter_by(
                allocation_id=alloc.id,
                billing_month=billing_date,
            ).first()

            if existing:
                skipped_count += 1
                continue

            due_date = date(billing_date.year, billing_date.month, due_day)
            charge = RentCharge(
                allocation_id=alloc.id,
                tenant_id=alloc.tenant_id,
                billing_month=billing_date,
                amount_due=alloc.monthly_rent_snapshot,
                due_date=due_date,
                status=RentStatus.PENDING,
            )
            db.session.add(charge)
            created_count += 1

        db.session.commit()
        click.secho(
            f"Rent generation complete for {billing_date.strftime('%B %Y')}: "
            f"{created_count} charges created, {skipped_count} existing charges skipped.",
            fg="green",
        )
