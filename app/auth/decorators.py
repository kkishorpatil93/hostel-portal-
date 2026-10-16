"""Role-based authorization decorators and helpers."""

from functools import wraps

from flask import abort, redirect, request, url_for
from flask_login import current_user


def owner_required(f):
    """Decorator to enforce authenticated OWNER role access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            target_next = request.full_path if request.query_string else request.path
            return redirect(url_for("auth.login", next=target_next))
        if not current_user.is_owner:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def tenant_required(f):
    """Decorator to restrict route access strictly to authenticated TENANT users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            target_next = request.full_path if request.query_string else request.path
            return redirect(url_for("auth.resident_login", next=target_next))
        if not current_user.is_tenant:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def get_own_or_404(model_class, record_id, tenant_id_field="tenant_id"):
    """Query a model by ID ensuring it belongs to current_user, or return 404.

    Prevents ID enumeration and unauthorized cross-tenant data access.
    """
    record = model_class.query.get(record_id)
    if not record:
        abort(404)
    # Owners can access any record
    if current_user.is_owner:
        return record
    # Tenants can only access their own records
    if getattr(record, tenant_id_field, None) != current_user.id:
        abort(404)
    return record
