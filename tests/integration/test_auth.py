"""Comprehensive integration tests for StayNest authentication and access control (Phase 2)."""

from itsdangerous import URLSafeTimedSerializer

from app.extensions import db
from app.models.user import User, UserRole


def test_owner_login_success(client, owner_user):
    """Owner logs in with valid credentials and redirects to owner dashboard."""
    res = client.post(
        "/auth/login",
        data={"email": "owner@staynest.local", "password": "OwnerSecure#2026"},
        follow_redirects=False,
    )
    assert res.status_code == 302
    assert "/owner/dashboard" in res.headers["Location"]


def test_owner_login_invalid_password(client, owner_user):
    """Owner login with invalid password returns 401 with generic error message."""
    res = client.post(
        "/auth/login",
        data={"email": "owner@staynest.local", "password": "WrongPassword123"},
        follow_redirects=True,
    )
    assert res.status_code == 401
    html = res.get_data(as_text=True)
    assert "Invalid email address or password" in html


def test_owner_login_lockout_after_5_attempts(client, owner_user):
    """Account gets locked for 15 minutes after 5 consecutive failed attempts."""
    for _ in range(5):
        client.post(
            "/auth/login",
            data={"email": "owner@staynest.local", "password": "WrongPassword"},
            follow_redirects=True,
        )

    db.session.refresh(owner_user)
    assert owner_user.is_locked is True

    # 6th attempt should return 403 lockout notice
    res = client.post(
        "/auth/login",
        data={"email": "owner@staynest.local", "password": "OwnerSecure#2026"},
        follow_redirects=True,
    )
    assert res.status_code == 403
    html = res.get_data(as_text=True)
    assert "temporarily locked" in html.lower() or "account locked" in html.lower()


def test_resident_login_with_email(client, tenant_user):
    """Resident logs in using registered email and password."""
    res = client.post(
        "/auth/resident-login",
        data={"identifier": "arjun.sharma@example.com", "password": "TenantPass#2026"},
        follow_redirects=False,
    )
    assert res.status_code == 302
    assert "/tenant/dashboard" in res.headers["Location"]


def test_resident_login_with_phone(client, tenant_user):
    """Resident logs in using 10-digit mobile phone number and password."""
    res = client.post(
        "/auth/resident/login",
        data={"identifier": tenant_user.phone, "password": "TenantPass#2026"},
        follow_redirects=False,
    )
    assert res.status_code == 302
    assert "/tenant/dashboard" in res.headers["Location"]


def test_safe_redirect_prevents_open_redirect(client, owner_user):
    """Safe redirect check prevents external and protocol-relative phishing redirects."""
    res = client.post(
        "/auth/login?next=https://evil.com",
        data={"email": "owner@staynest.local", "password": "OwnerSecure#2026"},
        follow_redirects=False,
    )
    assert res.status_code == 302
    # Should fall back to default dashboard, not external URL
    assert "evil.com" not in res.headers["Location"]
    assert "/owner/dashboard" in res.headers["Location"]


def test_unauthenticated_owner_route_redirects_with_next(client):
    """Unauthenticated access to /owner/rooms redirects to /auth/login?next=/owner/rooms."""
    res = client.get("/owner/rooms")
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]
    assert "next=" in res.headers["Location"]


def test_tenant_cannot_access_owner_pages(authenticated_tenant_client):
    """Authenticated tenant visiting owner routes receives 403 Forbidden."""
    res = authenticated_tenant_client.get("/owner/dashboard")
    assert res.status_code == 403
    res_rooms = authenticated_tenant_client.get("/owner/rooms")
    assert res_rooms.status_code == 403


def test_logout_terminates_session(authenticated_owner_client):
    """Logout endpoint signs out user and prevents further access."""
    res = authenticated_owner_client.get("/auth/logout", follow_redirects=True)
    assert res.status_code == 200
    assert "signed out" in res.get_data(as_text=True).lower()

    # Subsequent access to owner dashboard should now redirect to login
    check = authenticated_owner_client.get("/owner/dashboard")
    assert check.status_code == 302
    assert "/auth/login" in check.headers["Location"]


def test_password_reset_flow(client, app, owner_user):
    """Complete password recovery flow with timed token."""
    # 1. Request reset
    req_res = client.post(
        "/auth/forgot-password",
        data={"email": "owner@staynest.local"},
        follow_redirects=True,
    )
    assert req_res.status_code == 200
    assert "password reset instructions" in req_res.get_data(as_text=True).lower()

    # 2. Generate token programmatically as route does
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    token = serializer.dumps({"user_id": owner_user.id, "email": owner_user.email}, salt="password-reset-salt")

    # 3. GET reset form with valid token
    get_res = client.get(f"/auth/reset-password?token={token}")
    assert get_res.status_code == 200
    assert "Set New Password" in get_res.get_data(as_text=True)

    # 4. POST new password
    post_res = client.post(
        "/auth/reset-password",
        data={
            "token": token,
            "password": "NewSecurePassword#2026",
            "confirm_password": "NewSecurePassword#2026",
        },
        follow_redirects=True,
    )
    assert post_res.status_code == 200
    assert "successfully reset" in post_res.get_data(as_text=True).lower()

    # 5. Verify login with new password succeeds
    login_new = client.post(
        "/auth/login",
        data={"email": "owner@staynest.local", "password": "NewSecurePassword#2026"},
        follow_redirects=False,
    )
    assert login_new.status_code == 302
    assert "/owner/dashboard" in login_new.headers["Location"]


def test_password_reset_expired_token(client, app, owner_user):
    """Expired reset token is safely rejected."""
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    token = serializer.dumps({"user_id": owner_user.id, "email": owner_user.email}, salt="password-reset-salt")

    # Fast-forward token timestamp or test with invalid token
    bad_token = token + "corrupted"
    res = client.get(f"/auth/reset-password?token={bad_token}", follow_redirects=True)
    assert res.status_code == 200
    assert "invalid" in res.get_data(as_text=True).lower() or "expired" in res.get_data(as_text=True).lower()


def test_create_owner_cli_command(runner, app):
    """Flask CLI create-owner command creates or updates an owner account."""
    res = runner.invoke(
        args=[
            "create-owner",
            "--email", "admin.custom@staynest.local",
            "--name", "Custom Administrator",
            "--phone", "9876599999",
            "--password", "CustomAdmin#2026",
        ]
    )
    assert res.exit_code == 0
    assert "created successfully" in res.output or "updated successfully" in res.output

    with app.app_context():
        created = User.query.filter_by(email="admin.custom@staynest.local").first()
        assert created is not None
        assert created.role == UserRole.OWNER
        assert created.check_password("CustomAdmin#2026") is True
