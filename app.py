from flask import Flask, render_template, request, jsonify

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
