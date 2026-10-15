"""Settings, activity audit logs, and in-app notifications."""

import json
from datetime import datetime

from app.extensions import db


class SiteSetting(db.Model):
    """Dynamic site and business configuration parameters."""

    __tablename__ = "site_settings"

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_value(cls, key: str, default: str = "") -> str:
        try:
            setting = cls.query.filter_by(key=key).first()
            if setting and setting.value is not None:
                return setting.value
        except Exception:  # noqa: BLE001
            return default
        return default

    @classmethod
    def set_value(cls, key: str, value: str, description: str = "") -> None:
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            setting = cls(key=key, value=value, description=description)
            db.session.add(setting)
        db.session.commit()

    def __repr__(self):
        return f"<SiteSetting {self.key}={self.value}>"


class ActivityLog(db.Model):
    """Audit trail for administrative and tenant actions."""

    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = db.Column(db.String(100), nullable=False, index=True)  # e.g., "BOOKING_APPROVED", "PAYMENT_RECORDED"
    entity_type = db.Column(db.String(50), nullable=False)  # "Booking", "Allocation", "Payment"
    entity_id = db.Column(db.Integer, nullable=True)
    details_json = db.Column(db.Text, nullable=True)  # Clean sanitized JSON details
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    @property
    def details(self) -> dict:
        if not self.details_json:
            return {}
        try:
            return json.loads(self.details_json)
        except (json.JSONDecodeError, TypeError):
            return {}

    @details.setter
    def details(self, data: dict) -> None:
        self.details_json = json.dumps(data) if data else "{}"

    @classmethod
    def log(
        cls,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        user_id: int | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ):
        """Helper to create and persist an audit log entry."""
        log_entry = cls(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            ip_address=ip_address,
        )
        if details:
            log_entry.details = details
        db.session.add(log_entry)
        db.session.commit()
        return log_entry

    def __repr__(self):
        return f"<ActivityLog {self.action} on {self.entity_type} {self.entity_id}>"


class Notification(db.Model):
    """In-app alert notification dispatched to users."""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False, default="Notification")
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default="info")  # info, success, warning, alert
    link_url = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Notification for User {self.user_id}: {self.title} (Read: {self.is_read})>"
