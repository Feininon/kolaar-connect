import uuid

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from neo4j import exceptions

from database.neo4j_connection import driver, DATABASE
from models.user import User

auth_bp = Blueprint("auth", __name__)


def get_user_by_username(username):
    with driver.session(database=DATABASE) as session:
        result = session.run(
            """
            MATCH (u:User {username: $username})
            RETURN u
            """,
            username=username
        ).single()

        if result:
            u = result["u"]
            return User(u["user_id"], u["username"], u["email"], u["name"])

    return None


def get_user_by_id(user_id):
    with driver.session(database=DATABASE) as session:
        result = session.run(
            """
            MATCH (u:User {user_id: $user_id})
            RETURN u
            """,
            user_id=user_id
        ).single()

        if result:
            u = result["u"]
            return User(u["user_id"], u["username"], u["email"], u["name"])

    return None


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not all([name, username, email, password]):
            flash("All fields are required.")
            return redirect(url_for("auth.register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.")
            return redirect(url_for("auth.register"))

        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)

        try:
            with driver.session(database=DATABASE) as session:
                session.run(
                    """
                    CREATE (u:User {
                        user_id: $user_id,
                        name: $name,
                        username: $username,
                        email: $email,
                        password_hash: $password_hash,
                        created_at: datetime()
                    })
                    """,
                    user_id=user_id,
                    name=name,
                    username=username,
                    email=email,
                    password_hash=password_hash
                )

            flash("Registration successful. Please log in.")
            return redirect(url_for("auth.login"))

        except exceptions.ConstraintError:
            flash("Username or email already exists.")
            return redirect(url_for("auth.register"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with driver.session(database=DATABASE) as session:
            result = session.run(
                """
                MATCH (u:User {username: $username})
                RETURN u
                """,
                username=username
            ).single()

        if result:
            u = result["u"]

            if check_password_hash(u["password_hash"], password):
                user = User(
                    u["user_id"],
                    u["username"],
                    u["email"],
                    u["name"]
                )

                login_user(user)
                return redirect(url_for("home"))

        flash("Invalid username or password.")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))