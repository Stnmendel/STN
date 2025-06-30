import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Placeholder for user subscription check
SUBSCRIBED_USERS = {"demo@example.com"}

# Basic placeholder AI response
def ai_response(message):
    # This is a stub; integrate real model here
    return f"AetherAI echo: {message}"

# Example flight search using Skyscanner API (via RapidAPI or official API)
def query_skyscanner(origin, destination, depart, return_date=None, max_price=None):
    api_key = os.getenv("SKYSCANNER_API_KEY")
    if not api_key:
        # Return sample data when API key is missing
        return [
            {"airline": "DemoAir", "price": 199, "depart": depart, "arrive": depart},
            {"airline": "SampleJet", "price": 250, "depart": depart, "arrive": depart}
        ]

    try:
        # Placeholder example URL; replace with actual Skyscanner endpoint
        url = "https://partners.api.skyscanner.net/apiservices/v3/flights/live/search/create"
        headers = {"apikey": api_key}
        payload = {
            "query": {
                "market": "US",
                "locale": "en-US",
                "currency": "USD",
                "queryLegs": [{
                    "originPlaceId": {"iata": origin},
                    "destinationPlaceId": {"iata": destination},
                    "date": {"year": int(depart.split('-')[0]), "month": int(depart.split('-')[1]), "day": int(depart.split('-')[2])}
                }]
            }
        }
        if return_date:
            payload["query"]["queryLegs"].append({
                "originPlaceId": {"iata": destination},
                "destinationPlaceId": {"iata": origin},
                "date": {"year": int(return_date.split('-')[0]), "month": int(return_date.split('-')[1]), "day": int(return_date.split('-')[2])}
            })
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json()
        # Extract flights list from API response (simplified)
        flights = []
        for leg in results.get("content", {}).get("results", {}).get("itineraries", {}).values():
            price = leg.get("pricingOptions", [{}])[0].get("price", {}).get("amount")
            if max_price and price and price > float(max_price):
                continue
            flights.append({
                "airline": " / ".join(leg.get("carrierIds", [])),
                "price": price,
                "depart": depart,
                "arrive": leg.get("segments", [{}])[0].get("arrivalDateTime")
            })
        return flights
    except Exception as e:
        print("Skyscanner API error", e)
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(force=True)
    user = data.get('user')
    message = data.get('message')
    if user not in SUBSCRIBED_USERS:
        return jsonify({'error': 'User not subscribed'}), 403
    response = ai_response(message)
    return jsonify({'response': response})


@app.route('/flights')
def flights_page():
    return render_template('flights.html')


@app.route('/search_flights', methods=['POST'])
def search_flights():
    data = request.get_json(force=True)
    origin = data.get('origin')
    destination = data.get('destination')
    depart = data.get('depart')
    ret = data.get('return')
    max_price = data.get('max_price')
    if not origin or not destination or not depart:
        return jsonify({'error': 'Missing required fields'}), 400
    flights = query_skyscanner(origin, destination, depart, ret, max_price)
    return jsonify({'flights': flights})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

