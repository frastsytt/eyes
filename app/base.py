from flask import send_from_directory, send_file, Blueprint, render_template, redirect, url_for, session, jsonify, request, Response
import subprocess
from . import db 
from .auth import requires_roles
import jwt
import os
from datetime import datetime


base_bp = Blueprint('base', __name__)

# Anonymous Gregorian Algorithm for computing easter date
def compute_easter(year):
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    L = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * L) // 451
    month_easter = (h + L - 7 * m + 114) // 31  # 3 = mars, 4 = april
    day_easter = ((h + L - 7 * m + 114) % 31) + 1
    return month_easter, day_easter

@base_bp.route('/date', defaults={'fmt': None})
@base_bp.route('/date/<fmt>')
def get_date_format(fmt):
    today = datetime.today()
    special_message = ""
    if today.month == 12 and today.day == 25:
        special_message = "Merry Christmas!"
    elif today.month == 1 and today.day == 1:
        special_message = "Happy New Year!"
    else:
        easter_month, easter_day = compute_easter(today.year)
        if today.month == easter_month and today.day == easter_day:
            special_message = "Happy Easter!"

    if fmt:
        try:
            result = subprocess.check_output(f"date +{fmt}", shell=True, universal_newlines=True).strip()
            if special_message:
                result += " " + special_message + '\n'
            return Response(result, mimetype='text/plain')
        except subprocess.CalledProcessError as e:
            return Response(f"Error at getting the actual date: {e}", status=500, mimetype='text/plain')
    else:
        try:
            result = subprocess.check_output("date | grep -oE '[0-9]{4}'", shell=True, universal_newlines=True).strip()
            if special_message:
                result += " " + special_message +'\n'
            return Response(result, mimetype='text/plain')
        except subprocess.CalledProcessError as e:
            return Response(f"Error at getting the actual date: {e}", status=500, mimetype='text/plain')
