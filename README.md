# AetherAI Demo

This repository contains a simple Flask web application demonstrating an AI assistant called **AetherAI**. The application includes a basic chat interface and a placeholder subscription check.

It also includes a very basic drawing-based note feature inspired by apps like Goodnotes. Notes are stored in memory and displayed as images.

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
4. Visit `http://localhost:5000/notes` to try the drawing notes demo.

A single demo user `demo@example.com` is subscribed by default. Integrate your own subscription and AI logic as needed.
