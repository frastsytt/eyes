import json
import os
from datetime import datetime
import paho.mqtt.client as mqtt
from .models import ChatMessage, WebUser
import ssl
from sqlalchemy import text
from pymysql.constants import CLIENT

from . import db, create_app

app = create_app()
client = None


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        client.subscribe(os.getenv("MQTT_TOPIC_CHAT_SEND"))
        client.subscribe(os.getenv("MQTT_TOPIC_NOTIFICATION_SEND"))
    else:
        print("Connection failed with code:", rc)

def on_publish(client, userdata, mid, properties=None):
    print("Message published, mid:", mid)

def on_message(client, userdata, message):
    topic = message.topic
    payload_str = message.payload.decode('utf-8')

    try:
        data = json.loads(payload_str)
    except Exception as e:
        print("Parsing error..:", e)
        return
 
    topic_send = os.getenv("MQTT_TOPIC_CHAT_SEND")
    topic_notification_send = os.getenv("MQTT_TOPIC_NOTIFICATION_SEND")

    if topic == topic_send:
        message_text = data.get("message")
        email = data.get("userEmail")
        if not message_text or not email:
            return

        with app.app_context():
            try:
                user = WebUser.query.filter_by(email=email).first()
                if not user:
                    print("No user found...", email)
                    return              

                timestamp_to_save =  datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                query = text(f"INSERT INTO chat_message (web_user_id, timestamp, content) VALUES ( '{user.id}', '{timestamp_to_save}', '{message_text}')")
                result = db.session.execute(query)
                db.session.commit()

                broadcast_payload = json.dumps({
                    "message": message_text,
                    "username": user.username,
                    "timestamp": timestamp_to_save
                })

                topic_recv = os.getenv("MQTT_TOPIC_CHAT_RECV")
                client.publish(topic_recv, broadcast_payload)
            except Exception as e:
                print("Error at saving user...", e)


def start_mqtt():
    global client
    client = mqtt.Client(client_id="eyes_app_publisher", transport="websockets") 
    client.username_pw_set(username=os.getenv("MQTT_USERNAME"), password=os.getenv("MQTT_PASSWORD"))
    client.tls_set(
        cert_reqs=ssl.CERT_REQUIRED,  
        tls_version=ssl.PROTOCOL_TLS  
    )
    client.tls_insecure_set(False)  
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_message = on_message
    client.connect(os.getenv("MQTT_HOST"), int(os.getenv("MQTT_PORT")), keepalive=60)
    client.loop_start()


