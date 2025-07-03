# AetherAI Demo

This repository contains a simple Flask web application demonstrating an AI assistant called **AetherAI**. The application includes a basic chat interface, a barcode generator and a placeholder subscription check.

## Running the app

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   python app.py
  ```
3. Open `http://localhost:5000` in your browser.

The server's debug mode can be controlled via the `FLASK_DEBUG` environment variable. Set it to `1` to enable debug mode.

### Barcode API

POST `/barcode` with JSON `{ "data": "TEXT" }` or form data `data=TEXT` to receive a PNG barcode image.

A single demo user `demo@example.com` is subscribed by default. Integrate your own subscription and AI logic as needed.

