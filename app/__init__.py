from flask import Flask, render_template, Response
from dotenv import load_dotenv
import os
from flask_sqlalchemy import SQLAlchemy
from .url_config import UrlConfig 
from pymysql.constants import CLIENT
from paho.mqtt.client import Client

db = SQLAlchemy()

def create_app():
    load_dotenv()

    app = Flask(__name__, static_url_path=UrlConfig.DEFAULT_URL + 'static' if hasattr(UrlConfig, 'DEFAULT_URL') else 'static')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret')
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['SESSION_COOKIE_HTTPONLY'] = False
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['MQTT_HOST'] = os.getenv('MQTT_HOST')
    app.config['MQTT_PORT'] = os.getenv('MQTT_PORT')
    app.config['MQTT_PROXY_PORT'] = os.getenv('MQTT_PROXY_PORT')
    app.config['MQTT_USERNAME'] = os.getenv('MQTT_USERNAME')
    app.config['MQTT_PASSWORD'] = os.getenv('MQTT_PASSWORD')

    app.config['MQTT_TOPIC_CHAT_SEND'] = os.getenv('MQTT_TOPIC_CHAT_SEND')
    app.config['MQTT_TOPIC_CHAT_RECV'] = os.getenv('MQTT_TOPIC_CHAT_RECV')
    app.config['MQTT_TOPIC_NOTIFICATION_SEND'] = os.getenv('MQTT_TOPIC_NOTIFICATION_SEND')

    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'berylias_eyes')
    db_host = os.getenv('DB_HOST', 'localhost')

    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {
            'client_flag': 65536
        }
    }


    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
    )

    db.init_app(app)

    @app.after_request
    def add_csp(response):
        response.headers.pop('Content-Security-Policy', None)
        return response

    @app.context_processor
    def inject_mqtt_config():
        return {
            'mqtt_host': app.config.get('MQTT_HOST'),
            'mqtt_port': app.config.get('MQTT_PORT'),
            'mqtt_proxy_port': app.config.get('MQTT_PROXY_PORT'),
            'mqtt_username': app.config.get('MQTT_USERNAME'),
            'mqtt_password': app.config.get('MQTT_PASSWORD'),
            'mqtt_topic_chat_send': app.config.get('MQTT_TOPIC_CHAT_SEND'),
            'mqtt_topic_chat_recv': app.config.get('MQTT_TOPIC_CHAT_RECV'),
            'mqtt_topic_notification_send': app.config.get('MQTT_TOPIC_NOTIFICATION_SEND')
        }


    from .auth import auth_bp, oauth
    oauth.init_app(app)

    from .main import main_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    from .admin import admin_bp
    app.register_blueprint(admin_bp)

    from .extensions import extensions_bp
    app.register_blueprint(extensions_bp)

    from .base import base_bp
    app.register_blueprint(base_bp)

    from .profile import profile_bp
    app.register_blueprint(profile_bp)
    

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('500.html'), 500

    return app
