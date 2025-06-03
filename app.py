import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")

# Load subscribed users from environment variable
SUBSCRIBED_USERS = {u.strip().lower() for u in os.environ.get("AETHER_SUBSCRIBERS", "demo@example.com").split(',') if u.strip()}

# Basic placeholder AI response
def ai_response(message):
    # This is a stub; integrate real model here
    return f"AetherAI echo: {message}"

@app.route('/')
def index():
    if 'user' in session:
        return render_template('chat.html', user=session['user'], history=session.get('history', []))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if email in SUBSCRIBED_USERS:
            session['user'] = email
            session['history'] = []
            return redirect(url_for('index'))
        error = 'User not subscribed'
        return render_template('login.html', error=error), 403
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/chat', methods=['POST'])
def chat():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    data = request.get_json(force=True)
    message = data.get('message', '')
    response = ai_response(message)
    history = session.get('history', [])
    history.append({'user': message, 'bot': response})
    session['history'] = history
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
