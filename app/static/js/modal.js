document.addEventListener('DOMContentLoaded', function () {
    var modal = document.getElementById("notificationModal");
    var btn = document.getElementById("openNotificationModal");
    var span = document.getElementsByClassName("close")[0];
    var notificationList = document.getElementById("notificationList");

    btn.onclick = function () {
        updateNotificationPlaceholder();
        modal.style.display = "block";
    };

    span.onclick = function () {
        modal.style.display = "none";
    };

    window.onclick = function (event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    };

    function updateNotificationPlaceholder() {
        if (notificationList.children.length === 0) {
            var li = document.createElement("li");
            li.textContent = "No notifications";
            li.className = "placeholder";
            li.style.color = "#888";
            li.style.textAlign = "center";
            li.style.padding = "10px";
            notificationList.appendChild(li);
        }
    }

    function addNotification(title, filename, timestamp, shortDescription) {
        var placeholder = notificationList.querySelector("li.placeholder");
        if (placeholder) {
            notificationList.removeChild(placeholder);
        }

        var li = document.createElement("li");
        li.style.padding = "10px";
        li.style.marginBottom = "5px";
        li.style.borderBottom = "1px solid #ddd";
        li.style.backgroundColor = "#f9f9f9";
        li.style.borderRadius = "4px";

        var contentDiv = document.createElement("div");

        var link = document.createElement("a");
        link.href = "story/" + filename;
        link.innerHTML = title;
        link.style.color = "#3498db";
        link.style.textDecoration = "none";
        link.style.fontWeight = "600";
        link.target = "_blank";

        var timeSpan = document.createElement("span");
        var formattedTimestamp = timestamp.replace(' ', 'T') + 'Z';
        var date = new Date(formattedTimestamp);
        timeSpan.innerHTML = date.toLocaleString();
        timeSpan.style.fontSize = "0.85rem";
        timeSpan.style.color = "#555";

        contentDiv.appendChild(link);
        contentDiv.appendChild(document.createElement("br"));
        contentDiv.appendChild(timeSpan);

        if (shortDescription) {
            var words = shortDescription.split(/\s+/);
            if (words.length > 30) {
                shortDescription = words.slice(0, 30).join(" ") + " ...";
            }
            var descParagraph = document.createElement("p");
            descParagraph.innerHTML = shortDescription;
            descParagraph.style.margin = "5px 0 0 0";
            descParagraph.style.fontSize = "0.9rem";
            descParagraph.style.color = "#333";
            descParagraph.style.textAlign = "justify";
            contentDiv.appendChild(document.createElement("br"));
            contentDiv.appendChild(descParagraph);
        }

        li.appendChild(contentDiv);

        if (notificationList.firstChild) {
            notificationList.insertBefore(li, notificationList.firstChild);
        } else {
            notificationList.appendChild(li);
        }

        while (notificationList.children.length > 3) {
            notificationList.removeChild(notificationList.lastChild);
        }

        modal.style.display = "block";
    }

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
        if (message.destinationName === MQTT_TOPIC_NOTIFICATION_SEND) {
            try {
                const data = JSON.parse(message.payloadString);
                addNotification(data.title, data.filename, data.timestamp, data.short_description);
            } catch (e) {
                console.error("Error parsing notification message:", e);
            }
        }
    };

    mqttClient.connect({
        userName: MQTT_USERNAME,
        password: MQTT_PASSWORD,
        onSuccess: function () {
            mqttClient.subscribe(MQTT_TOPIC_NOTIFICATION_SEND);
        },
        onFailure: function (err) {
            console.error("Failed to connect to MQTT broker:", err);
        }
    });
});
