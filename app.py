from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Placeholder for user subscription check
SUBSCRIBED_USERS = {"demo@example.com"}

NOTES = []  # simple in-memory store for saved notes

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


@app.route('/notes')
def notes_page():
    return render_template('notes.html')


@app.route('/notes', methods=['POST'])
def save_note():
    data = request.get_json(force=True)
    image = data.get('image')
    if not image:
        return jsonify({'error': 'no image'}), 400
    NOTES.append(image)
    return jsonify({'status': 'saved'})


@app.route('/notes/list')
def list_notes():
    return jsonify({'notes': NOTES})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
