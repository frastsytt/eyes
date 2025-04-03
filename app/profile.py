import os
from functools import wraps
from flask import (
    request,
    Blueprint,
    redirect,
    url_for,
    session,
    jsonify,
    render_template,
    g,
    render_template_string,
)
from authlib.integrations.flask_client import OAuth
import uuid
import jwt
import time
import requests
import imghdr

from .models import WebUser
from . import db
from .auth import requires_roles

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile", methods=["GET", "POST"])
@requires_roles("admin", "user")
def profile():
    user_role = g.get("user_role", None)
    user = session.get("user")
    if not user:
        return render_template("404.html"), 404

    email = user.get("email")
    if not email:
        return render_template("404.html"), 404

    existing_user = WebUser.query.filter_by(email=email).first()
    if not existing_user:
        return render_template("404.html"), 404

    if request.method == "GET":
        username = render_template_string(existing_user.username)
        return_user = {
            "real_name": user.get("name"),
            "username": existing_user.username,
            "email": existing_user.email,
            "profile_image": existing_user.user_image,
        }
        return render_template(
            "profile.html",
            username=username,
            admin_role=user_role,
            title="Profile",
            userinfo=return_user,
            user_email=email,
        )

    if request.method == "POST":
        display_name = request.form.get("displayName")
        if display_name != existing_user.username and display_name != "":
            existing_user.username = display_name

        if "avatarUpload" in request.files:
            if request.files["avatarUpload"].filename != "":
                upload_base = "/opt/eyes/app/static/images/profile"
                old_photo_path = os.path.join(upload_base, existing_user.user_image)
                try:
                    if existing_user.user_image != "avatar.png":
                        remove_old_photos = f"rm -f {old_photo_path}"
                        os.popen(remove_old_photos)
                except Exception as e:
                    print("Error deleting old user profile photo!")

                upload_base = "/opt/eyes/app/static/images/profile"
                file = request.files["avatarUpload"]
                unique_identifier = str(uuid.uuid4())
                filename = f"{unique_identifier}_{file.filename}"
                filepath = os.path.join(upload_base, filename)
                file.save(filepath)

                try:
                    check_image_upload = f"file {filepath}"
                    if not os.path.isfile(filepath):
                        raise FileNotFoundError(f"File {filepath} not found.")
                    existing_user.user_image = filename
                except Exception as e:
                    existing_user.user_image = "avatar.png"

        db.session.commit()

        return redirect(url_for("profile.profile"))

    return render_template("404.html"), 404
