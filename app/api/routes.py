"""Public and authenticated JSON API endpoints."""

from flask import jsonify

from app.api import api_bp
from app.models.property import Room


@api_bp.route("/rooms", methods=["GET"])
def get_rooms():
    """Public read-only API endpoint returning available rooms with pricing and amenities."""
    rooms = Room.query.filter_by(is_active=True).all()
    data = []
    for r in rooms:
        data.append(
            {
                "id": r.id,
                "room_number": r.room_number,
                "room_type": r.room_type,
                "floor": r.floor,
                "capacity": r.capacity,
                "available_beds": r.available_beds,
                "monthly_rent": float(r.monthly_rent),
                "security_deposit": float(r.security_deposit),
                "amenities": [a.name for a in r.amenities],
            }
        )
    return jsonify({"success": True, "rooms": data, "count": len(data)})
