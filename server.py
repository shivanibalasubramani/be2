from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import random
from twilio.rest import Client

app = Flask(__name__)
CORS(app)

ORS_API_KEY = "5b3ce3597851110001cf6248c9c1caf0c5184c1eb25fbafbffec22aa"
TWILIO_SID = "ACe753008ce457480071e226a96cff7499"
TWILIO_AUTH = "f0fae571241469cffdea3f9cdfc88cae"
TWILIO_PHONE = "+12544143692"
EMERGENCY_CONTACT = "+917845433488"

def get_routes(start, end):
    """Fetches multiple alternative routes between start and end locations."""
    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    
    body = {
        "coordinates": [[start[1], start[0]], [end[1], end[0]]],
        "alternative_routes": {"target_count": 3, "share_factor": 0.7},
        "format": "geojson"
    }

    response = requests.post(url, json=body, headers=headers)
    
    try:
        data = response.json()
        if "features" not in data:
            return {"error": "No routes found", "response": data}

        routes = []
        for feature in data["features"]:
            coordinates = [(point[1], point[0]) for point in feature["geometry"]["coordinates"]]
            safety_score = random.randint(1, 10)  # Random safety score from 1 to 10
            routes.append({
                "coordinates": coordinates,
                "safety_score": safety_score,
                "start": start,  # Add start point for alert message
                "end": end       # Add end point for alert message
            })

        return routes
    except Exception as e:
        return {"error": "API response error", "details": str(e)}

@app.route("/route", methods=["POST"])
def route():
    """Handles route request and returns multiple options with safety scores."""
    data = request.json
    start, end = data.get("start"), data.get("end")

    if not start or not end:
        return jsonify({"error": "Missing start or end coordinates"}), 400

    route_options = get_routes(start, end)

    if isinstance(route_options, dict) and "error" in route_options:
        return jsonify(route_options), 500

    return jsonify({"routes": route_options})

@app.route("/send_alert", methods=["POST"])
def send_alert():
    """Sends an SMS alert when a route is selected."""
    data = request.json
    selected_route = data.get("route")

    if not selected_route:
        return jsonify({"error": "No route selected"}), 400

    # Get the start, end, and safety score from selected_route
    start = selected_route.get("start")
    end = selected_route.get("end")
    safety_score = selected_route.get("safety_score")

    # Determine the safety level for the alert
    if safety_score >= 7:
        safety_level = "very safe"
    elif safety_score <= 6 and safety_score >= 4:
        safety_level = "mildly safe"
    else:
        safety_level = "Risky"

    client = Client(TWILIO_SID, TWILIO_AUTH)
    message = client.messages.create(
        body=f"Your friend is traveling from {start} to {end} via a route that is {safety_level}",
        from_=TWILIO_PHONE,
        to=EMERGENCY_CONTACT
    )

    return jsonify({"message": "Alert Sent!", "message_sid": message.sid})

if __name__ == "__main__":
    app.run(debug=True, port=5001)