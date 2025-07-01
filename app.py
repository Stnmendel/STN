from flask import Flask, render_template, request, jsonify, abort

app = Flask(__name__)

# Placeholder for user subscription check (for chat feature)
SUBSCRIBED_USERS = {"demo@example.com"}

# Sample blog posts (would normally come from a database)
POSTS = [
    {
        "id": 1,
        "title": "Hoşgeldiniz: Yeni Blogumuza Göz Atın",
        "content": "<p>Bu bir deneme içeriğidir. Onedio tarzı için basit bir örnek.</p>",
        "image": "https://via.placeholder.com/800x400",
    },
    {
        "id": 2,
        "title": "Trendlerde Bugün: En Popüler 10 Haber",
        "content": "<p>Günün en popüler içeriklerini sizler için derledik.</p>",
        "image": "https://via.placeholder.com/800x400?text=Trend",
    },
]

TRENDING_IDS = [2]

# Basic placeholder AI response for chat

def ai_response(message):
    return f"AetherAI echo: {message}"

@app.route("/")
def index():
    trending = [p for p in POSTS if p["id"] in TRENDING_IDS]
    return render_template("index.html", posts=POSTS, trending=trending)

@app.route("/post/<int:post_id>")
def post_detail(post_id):
    post = next((p for p in POSTS if p["id"] == post_id), None)
    if not post:
        abort(404)
    return render_template("post.html", post=post)

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
