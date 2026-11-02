import os
from flask import Flask, redirect, url_for
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
from routes.notifications import notifications_bp

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

for blueprint in (auth_bp, profile_bp, posts_bp, discovery_bp, graph_bp,
                  analytics_bp, hashtags_bp, notifications_bp):
    app.register_blueprint(blueprint)

@app.route("/")
def home():
    return redirect(url_for("posts.feed")) if current_user.is_authenticated else redirect(url_for("auth.login"))

if __name__ == "__main__":
    verify_connection()
    app.run(debug=True)
