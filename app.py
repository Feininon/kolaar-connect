import os

from flask import Flask
from flask_login import LoginManager, current_user
from dotenv import load_dotenv

from database.neo4j_connection import verify_connection
from routes.auth import auth_bp, get_user_by_id
from routes.profile import profile_bp
from routes.posts import posts_bp
from routes.discovery import discovery_bp
from routes.graph import graph_bp
from routes.analytics import analytics_bp
from routes.hashtags import hashtags_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)


app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(posts_bp)
app.register_blueprint(discovery_bp)
app.register_blueprint(graph_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(hashtags_bp)

@app.route("/")
def home():
    if current_user.is_authenticated:
        return f"Welcome to Kolaar Connect, {current_user.username}!"
    return "Kolaar Connect Backend Running! <a href='/login'>Login</a>"


if __name__ == "__main__":
    verify_connection()
    app.run(debug=True)