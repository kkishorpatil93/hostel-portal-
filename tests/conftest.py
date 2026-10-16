"""Pytest fixtures for StayNest PG platform."""

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture(autouse=True)
def app():
    """Create application configured for testing with an in-memory SQLite database and pushed app context."""
    app_instance = create_app("testing")
    ctx = app_instance.app_context()
    ctx.push()
    db.create_all()

    yield app_instance

    db.session.remove()
    db.drop_all()
    ctx.pop()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def owner_user(app):
    """Return an active Owner user in the test database."""
    from app.models.user import User, UserRole
    owner = User.query.filter_by(role=UserRole.OWNER).first()
    if not owner:
        owner = User(
            full_name="Rajesh Sharma (Owner)",
            email="owner@staynest.local",
            phone="9876543210",
            role=UserRole.OWNER,
            is_active=True,
            email_verified=True,
        )
        owner.set_password("OwnerSecure#2026")
        db.session.add(owner)
        db.session.commit()
    return owner


@pytest.fixture
def tenant_user(app):
    """Return an active Tenant user in the test database."""
    from app.models.user import User, UserRole
    tenant = User.query.filter_by(role=UserRole.TENANT).first()
    if not tenant:
        tenant = User(
            full_name="Arjun Sharma",
            email="arjun.sharma@example.com",
            phone="9876500001",
            role=UserRole.TENANT,
            is_active=True,
            email_verified=True,
        )
        tenant.set_password("TenantPass#2026")
        db.session.add(tenant)
        db.session.commit()
    return tenant


@pytest.fixture
def authenticated_owner_client(client, owner_user):
    """Test client authenticated as Owner."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(owner_user.id)
        sess["_fresh"] = True
    return client


@pytest.fixture
def authenticated_tenant_client(client, tenant_user):
    """Test client authenticated as Tenant."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(tenant_user.id)
        sess["_fresh"] = True
    return client
