#!/usr/bin/env python
"""One-time setup script to initialize or reset an Owner/Administrator account for StayNest PG.

Usage:
    python scripts/create_owner.py
    python scripts/create_owner.py --email owner@example.com --name "Owner Name" --phone 9876543210 --password "MySecret#2026"
"""

import argparse
import getpass
import os
import sys

# Ensure project root is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from app.extensions import db
from app.models.user import User, UserRole


def main():
    parser = argparse.ArgumentParser(description="Create or update StayNest Owner account.")
    parser.add_argument("--email", help="Owner email address")
    parser.add_argument("--name", help="Owner full name")
    parser.add_argument("--phone", help="Owner contact phone number")
    parser.add_argument("--password", help="Owner password (min 8 characters)")
    args = parser.parse_args()

    email = (args.email or input("Owner Email Address: ")).strip().lower()
    if not email or "@" not in email:
        print("Error: A valid email address is required.")
        sys.exit(1)

    name = (args.name or input("Full Name [PG Administrator]: ")).strip() or "PG Administrator"
    phone = (args.phone or input("Phone Number [9876543210]: ")).strip() or "9876543210"

    password = args.password
    if not password:
        while True:
            p1 = getpass.getpass("New Password (min 8 characters): ")
            if len(p1) < 8:
                print("Error: Password must be at least 8 characters long.")
                continue
            p2 = getpass.getpass("Confirm New Password: ")
            if p1 != p2:
                print("Error: Passwords do not match. Try again.")
                continue
            password = p1
            break
    elif len(password) < 8:
        print("Error: Password must be at least 8 characters long.")
        sys.exit(1)

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            user.full_name = name
            user.phone = phone
            user.role = UserRole.OWNER
            user.is_active = True
            user.email_verified = True
            user.set_password(password)
            user.reset_failed_logins()
            db.session.commit()
            print(f"\n[SUCCESS] Existing user '{email}' was updated with OWNER role and new password.")
        else:
            owner = User(
                full_name=name,
                email=email,
                phone=phone,
                role=UserRole.OWNER,
                is_active=True,
                email_verified=True,
            )
            owner.set_password(password)
            db.session.add(owner)
            db.session.commit()
            print(f"\n[SUCCESS] Owner account '{email}' created successfully.")


if __name__ == "__main__":
    main()
