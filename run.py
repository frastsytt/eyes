from app import create_app, db
from app.mqtt_client import start_mqtt
import os

app = create_app()

with app.app_context():
    db.create_all()

start_mqtt()

if __name__ == "__main__":
    app.run(host=os.getenv('SERVER_HOST'), port = os.getenv('SERVER_PORT'), debug=os.getenv('SERVER_DEBUG'))