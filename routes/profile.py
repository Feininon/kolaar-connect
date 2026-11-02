
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from database.neo4j_connection import driver, DATABASE

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile")
@login_required
def my_profile():
    return redirect(
        url_for(
            "profile.view_profile",
            username=current_user.username
        )
    )

@profile_bp.route("/profile/<username>")
@login_required
def view_profile(username):
    with driver.session(database=DATABASE) as session:
        result = session.run(
            """
            MATCH (u:User {username: $username})
            OPTIONAL MATCH (u)<-[:FOLLOWS]-(follower:User)
            WITH u, count(DISTINCT follower) AS followers
            OPTIONAL MATCH (u)-[:FOLLOWS]->(following:User)
            RETURN u, followers, count(DISTINCT following) AS following
            """,
            username=username
        ).single()

    if not result:
        flash("User not found.")
        return redirect(url_for("home"))

    user = dict(result["u"])
    user["followers"] = result["followers"]
    user["following"] = result["following"]

    is_following = False

    if current_user.username != username:
        with driver.session(database=DATABASE) as session:
            is_following = session.run(
                """
                MATCH (:User {user_id: $me})-[:FOLLOWS]->
                      (:User {username: $target})
                RETURN count(*) > 0 AS following
                """,
                me=current_user.id,
                target=username
            ).single()["following"]

    return render_template(
        "profile.html",
        user=user,
        is_following=is_following
    )


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        bio = request.form.get("bio", "").strip()

        if not name:
            flash("Name cannot be empty.")
            return redirect(url_for("profile.edit_profile"))

        with driver.session(database=DATABASE) as session:
            session.run(
                """
                MATCH (u:User {user_id: $user_id})
                SET u.name = $name,
                    u.bio = $bio
                """,
                user_id=current_user.id,
                name=name,
                bio=bio
            )

        flash("Profile updated!")
        return redirect(
            url_for("profile.view_profile",
                    username=current_user.username)
        )

    with driver.session(database=DATABASE) as session:
        result = session.run(
            """
            MATCH (u:User {user_id: $user_id})
            RETURN u
            """,
            user_id=current_user.id
        ).single()

    user = dict(result["u"])
    return render_template("edit_profile.html", user=user)


@profile_bp.route("/follow/<username>", methods=["POST"])
@login_required
def follow_user(username):
    if username == current_user.username:
        flash("You cannot follow yourself.")
        return redirect(url_for("profile.view_profile",
                                username=username))

    with driver.session(database=DATABASE) as session:
        session.run(
            """
            MATCH (me:User {user_id: $me})
            MATCH (target:User {username: $target})
            MERGE (me)-[:FOLLOWS]->(target)
            """,
            me=current_user.id,
            target=username
        )

    return redirect(url_for("profile.view_profile",
                            username=username))


@profile_bp.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow_user(username):
    with driver.session(database=DATABASE) as session:
        session.run(
            """
            MATCH (me:User {user_id: $me})-[r:FOLLOWS]->
                 (target:User {username: $target})
            DELETE r
            """,
            me=current_user.id,
            target=username
        )

    return redirect(url_for("profile.view_profile",
                            username=username))
