# AetherAI Demo

This repository contains a small Flask web application demonstrating an AI assistant called **AetherAI**. The app now includes a simple login flow, a chat interface that remembers conversation history, and a configurable list of subscribed users.

## Running the app

1. Install dependencies from `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
2. Optionally set subscribed users via the `AETHER_SUBSCRIBERS` environment variable (comma separated emails). The default is `demo@example.com`.
3. Start the server:
   ```bash
   python app.py
   ```
4. Open `http://localhost:5000` in your browser and log in with one of the subscribed email addresses.

The default subscriber list contains only `demo@example.com`. Integrate your own subscription management and AI logic as needed.
