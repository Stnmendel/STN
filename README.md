# AetherAI Demo

This repository contains a simple Flask web application demonstrating an AI assistant called **AetherAI**. The application includes a basic chat interface and a placeholder subscription check.

## Running the app

1. Install dependencies:
   ```bash
   pip install flask
   ```
2. Start the server:
   ```bash
   python app.py
   ```
3. Open `http://localhost:5000` in your browser.

A single demo user `demo@example.com` is subscribed by default. Integrate your own subscription and AI logic as needed.

## Fetching Businesses from Google

To retrieve business details by category using the Google Places API, use the provided `google_fetch.py` script. Set your API key in the `GOOGLE_API_KEY` environment variable and run:

```bash
pip install googlemaps
python google_fetch.py "restaurants" --location "40.7128,-74.0060" --radius 1000
```

This will print the name, address, phone, website and a simple summary of comments for each result.
