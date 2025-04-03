import os
from functools import wraps
from flask import Blueprint, redirect, url_for, session, jsonify, render_template, g
from authlib.integrations.flask_client import OAuth
from uuid import uuid4
import jwt
import time
import requests

from .models import WebUser
from . import db

auth_bp = Blueprint('auth', __name__)

oauth = OAuth()

KEYCLOAK_SERVER = os.getenv("KEYCLOAK_SERVER")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

discovery_url = f"{KEYCLOAK_SERVER.rstrip('/')}/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration"

oauth.register(
    name='keycloak',
    client_id=KEYCLOAK_CLIENT_ID,
    client_secret=KEYCLOAK_CLIENT_SECRET,
    server_metadata_url=discovery_url,
    client_kwargs={'scope': 'openid profile email groups'}
)

@auth_bp.route('/login')
def login():
    if session.get('token') and session.get('user'):
        token = session['token']
        access_token_str = token.get('access_token')
        if not access_token_str:
            return redirect(url_for('main.welcome'))
        try:
            decoded_access = jwt.decode(
                access_token_str,
                options={"verify_signature": False, "verify_exp": False}
            )
        except Exception as e:
            print("Error at decoding the token.", e)
            return redirect(url_for('main.welcome'))

        resource_access = decoded_access.get('resource_access', {})
      
        roles = resource_access.get(KEYCLOAK_CLIENT_ID, {}).get('roles', [])
        
        if 'admin' in roles:
            return redirect(url_for('admin.admin'))
        elif 'user' in roles:
            return redirect(url_for('main.user'))
        else:
            return redirect(url_for('main.welcome'))

    nonce = generate_nonce() 
    session['nonce'] = nonce 
    redirect_uri = url_for('auth.callback', _external=True, _scheme='https')
    return oauth.keycloak.authorize_redirect(redirect_uri, nonce=nonce)

@auth_bp.route('/user/oauth2/callback')
def callback():
    token = oauth.keycloak.authorize_access_token()
    nonce = session.get('nonce')
    if not nonce:
        return jsonify({"error": "Missing nonce."}), 400

    user_info = oauth.keycloak.parse_id_token(token, nonce=nonce)
    session['user'] = user_info
    session['token'] = token

    
    access_token_str = token.get('access_token')
    if not access_token_str:
        return redirect(url_for('main.welcome'))
    try:
        decoded_access = jwt.decode(
            access_token_str,
            options={"verify_signature": False, "verify_exp": False}
        )
    except Exception as e:
        print("Error at decoding the token.", e)
        return redirect(url_for('main.welcome'))

    resource_access = decoded_access.get('resource_access', {})
    roles = resource_access.get(KEYCLOAK_CLIENT_ID, {}).get('roles', [])

    if 'admin' in roles or 'user' in roles:
        if user_info.get('email'):
            existing_user = WebUser.query.filter_by(email=user_info.get('email')).first()
            if not existing_user:
                new_user = WebUser(username=user_info.get('name'), email=user_info.get('email'), user_image='avatar.png')
                db.session.add(new_user)
                db.session.commit()

    if 'admin' in roles:
        return redirect(url_for('admin.admin'))
    elif 'user' in roles:
        return redirect(url_for('main.user'))
    else:
        return redirect(url_for('main.welcome'))

@auth_bp.route('/userdata')
def profile():
    user = session.get('user')
    token = session.get('token')
    if not user or not token:
        return jsonify({"error": "User is not authenticated."}), 401

    return jsonify({
        "user_info": user,
        "token": token
    })

def requires_roles(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = session.get('token')
            if not token:
                return redirect(url_for('main.welcome'))
            
            access_token_str = token.get('access_token')
            if not access_token_str:
                return redirect(url_for('main.welcome'))
            
            try:
                decoded_access = jwt.decode(
                    access_token_str,
                    options={"verify_signature": False, "verify_exp": False}
                )
            except Exception as e:
                print("Error at decoding the token.", e)
                return redirect(url_for('main.welcome'))
            
            exp = decoded_access.get("exp")
            if not exp or exp < time.time():
                session.clear()
                return render_template("login.html", title="Login", expired=True)
            
            resource_access = decoded_access.get('resource_access', {})
            eyes_roles = resource_access.get(KEYCLOAK_CLIENT_ID, {}).get('roles', [])
            
            if any(role in eyes_roles for role in roles):
                g.user_role = eyes_roles[0]
                return f(*args, **kwargs)
            
            return render_template('404.html'), 404
        return decorated_function
    return decorator

def generate_nonce():
    nonce = os.getenv('NONCE')
    return nonce

@auth_bp.route('/logout')
def logout():

    id_token = session.get('token', {}).get('id_token')
    session.clear()


    keycloak_logout_url = (
        f"{KEYCLOAK_SERVER.rstrip('/')}/realms/{KEYCLOAK_REALM}"
        f"/protocol/openid-connect/logout"
        f"?post_logout_redirect_uri={url_for('main.welcome', _external=True,_scheme='https')}"
    )

    if id_token:
        keycloak_logout_url += f"&id_token_hint={id_token}"
    else:
        return redirect(url_for('main.welcome'))

    
    return redirect(keycloak_logout_url)

