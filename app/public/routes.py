"""Public views: Home, Rooms catalog, Room details, Amenities, Contact, FAQ, Tour request."""

from flask import Response, render_template, request

from app.models.operations import Review
from app.models.property import Amenity, Property, Room
from app.public import public_bp


@public_bp.route("/")
def index():
    property_obj = Property.query.first()
    featured_rooms = Room.query.filter_by(is_active=True).limit(6).all()
    amenities = Amenity.query.all()
    approved_reviews = Review.query.filter_by(is_approved=True).limit(4).all()
    return render_template(
        "public/index.html",
        property=property_obj,
        rooms=featured_rooms,
        amenities=amenities,
        reviews=approved_reviews,
    )


@public_bp.route("/about")
def about():
    property_obj = Property.query.first()
    return render_template("public/about.html", property=property_obj)


@public_bp.route("/rooms")
def rooms():
    room_type = request.args.get("type", "").strip()
    query = Room.query.filter_by(is_active=True)
    if room_type:
        query = query.filter(Room.room_type.ilike(f"%{room_type}%"))
    all_rooms = query.all()
    return render_template("public/rooms.html", rooms=all_rooms, selected_type=room_type)


@public_bp.route("/rooms/<int:room_id>")
def room_detail(room_id):
    room = Room.query.get_or_404(room_id)
    return render_template("public/room_detail.html", room=room)


@public_bp.route("/amenities")
def amenities():
    all_amenities = Amenity.query.all()
    return render_template("public/amenities.html", amenities=all_amenities)


@public_bp.route("/contact")
def contact():
    property_obj = Property.query.first()
    return render_template("public/contact.html", property=property_obj)


@public_bp.route("/faq")
def faq():
    return render_template("public/faq.html")


@public_bp.route("/tour")
def tour():
    rooms = Room.query.filter_by(is_active=True).all()
    return render_template("public/tour.html", rooms=rooms)


@public_bp.route("/privacy")
def privacy():
    return render_template("public/privacy.html")


@public_bp.route("/terms")
def terms():
    return render_template("public/terms.html")


@public_bp.route("/robots.txt")
def robots_txt():
    content = "User-agent: *\nAllow: /\nDisallow: /owner/\nDisallow: /tenant/\nDisallow: /api/\nSitemap: /sitemap.xml\n"
    return Response(content, mimetype="text/plain")


@public_bp.route("/sitemap.xml")
def sitemap_xml():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>/</loc><priority>1.0</priority></url>
  <url><loc>/rooms</loc><priority>0.9</priority></url>
  <url><loc>/amenities</loc><priority>0.8</priority></url>
  <url><loc>/about</loc><priority>0.7</priority></url>
  <url><loc>/contact</loc><priority>0.7</priority></url>
  <url><loc>/faq</loc><priority>0.6</priority></url>
</urlset>"""
    return Response(xml, mimetype="application/xml")
