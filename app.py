import os
from io import BytesIO

from flask import Flask, render_template, request, jsonify, send_file
import barcode
from barcode.writer import ImageWriter

app = Flask(__name__)

# Placeholder for user subscription check
SUBSCRIBED_USERS = {"demo@example.com"}

# Basic placeholder AI response
def ai_response(message):
    # This is a stub; integrate real model here
    return f"AetherAI echo: {message}"

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


@app.route('/barcode', methods=['POST'])
def generate_barcode():
    data = request.form.get('data')
    if not data:
        json_data = request.get_json(silent=True)
        if json_data:
            data = json_data.get('data')
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    code128 = barcode.get('code128', data, writer=ImageWriter())
    buffer = BytesIO()
    code128.write(buffer)
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png')

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', '0') in ('1', 'True', 'true')
    app.run(debug=debug_mode, host='0.0.0.0')
