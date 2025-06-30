# AetherAI Demo

This repository contains a simple Flask web application demonstrating an AI assistant called **AetherAI**. The application now also includes a basic flight search demo alongside the chat interface. The flight search page integrates with the Skyscanner API when an API key is provided or falls back to sample data for demonstration.

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
4. Visit `/flights` for the flight search demo.

To enable real flight search, set the environment variable `SKYSCANNER_API_KEY` with your API key.

A single demo user `demo@example.com` is subscribed by default. Integrate your own subscription and AI logic as needed.
