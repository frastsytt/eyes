document.addEventListener('DOMContentLoaded', function () {

    const chatIcon = document.getElementById('chatIcon');
    const chatWindow = document.getElementById('chatWindow');
    const closeChat = document.getElementById('closeChat');
    const sendChat = document.getElementById('sendChat');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');

    chatIcon.addEventListener('click', () => {
        if (chatWindow.style.display === 'flex') {
            chatWindow.style.display = 'none';
        } else {
            chatWindow.style.display = 'flex';
        }
    });

    closeChat.addEventListener('click', () => {
        chatWindow.style.display = 'none';
    });

    const clientId = "client_" + Math.floor(Math.random() * 1000);
    const url = "wss://" + MQTT_HOST + ":" + MQTT_PROXY_PORT + "/";

    let mqttClient;
    try {
        mqttClient = new Paho.Client(url, clientId);
    } catch (err) {
        console.error("Error creating MQTT client:", err.message);
    }

    if (!mqttClient) {
        console.error("MQTT client was not created.");
        return;
    }

    mqttClient.onConnectionLost = function (responseObject) {
        if (responseObject.errorCode !== 0) {
            console.error("Connection lost:", responseObject.errorMessage);
        }
    };

    mqttClient.onMessageArrived = function (message) {
        try {
            const data = JSON.parse(message.payloadString);
            addMessageToChat(data.message, data.timestamp, data.username);
        } catch (e) {
            console.error("Error at parsing MQTT message:", e);
        }
    };

    mqttClient.connect({
        userName: MQTT_USERNAME,
        password: MQTT_PASSWORD,
        onSuccess: function () {
            mqttClient.subscribe(MQTT_TOPIC_CHAT_RECV);
        },
        onFailure: function (err) {
            console.error("Failed to connect to MQTT broker:", err);
        }
    });

    sendChat.addEventListener('click', () => {
        const message = chatInput.value;
        if (message) {
            const now = new Date();
            const timeString = now.toLocaleString();

            const payload = JSON.stringify({
                message: message,
                userEmail: user_email
            });
            const mqttMessage = new Paho.Message(payload);

            mqttMessage.destinationName = MQTT_TOPIC_CHAT_SEND;
            mqttClient.send(mqttMessage);


            chatInput.value = '';
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    });

    chatInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendChat.click();
        }
    });

    function addMessageToChat(message, timestamp, userId) {
        const msgDiv = document.createElement('div');
        msgDiv.style.margin = '5px 0';
        msgDiv.style.padding = '5px';
        msgDiv.style.borderBottom = '1px solid #ccc';

        const contentDiv = document.createElement('div');
        contentDiv.innerHTML = message;
        contentDiv.style.marginBottom = '5px';

        const metaDiv = document.createElement('div');
        metaDiv.style.fontSize = '0.85rem';
        metaDiv.style.color = '#555';
        var formattedTimestamp = timestamp.replace(' ', 'T') + 'Z';
        var date = new Date(formattedTimestamp);
        metaDiv.innerHTML = `<strong> ${userId}</strong> • ${date.toLocaleString()}`;

        msgDiv.appendChild(contentDiv);
        msgDiv.appendChild(metaDiv);

        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
