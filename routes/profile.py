from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from database.neo4j_connection import driver, DATABASE
from routes.notifications import create_notification

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile")
@login_required
def my_profile():
    return redirect(url_for("profile.profile", username=current_user.username))

@profile_bp.route("/profile/<username>")
@login_required
def profile(username):
    with driver.session(database=DATABASE) as session:
        user_record = session.run("""
            MATCH (u:User {username: $username})
            OPTIONAL MATCH (u)-[:CREATED]->(p:Post)
            WITH u, count(DISTINCT p) AS post_count
            OPTIONAL MATCH (follower:User)-[:FOLLOWS]->(u)
            WITH u, post_count, count(DISTINCT follower) AS follower_count
            OPTIONAL MATCH (u)-[:FOLLOWS]->(following:User)
            RETURN u.user_id AS user_id, u.username AS username,
                   u.name AS name, u.bio AS bio,
                   post_count AS posts, follower_count AS followers,
                   count(DISTINCT following) AS following
            """, username=username).single()
        if not user_record:
            flash("User not found.")
            return redirect(url_for("posts.feed"))
        user = user_record.data()
        is_following = False
        if current_user.id != user["user_id"]:
            check = session.run("""
                MATCH (me:User {user_id:$me_id}), (target:User {user_id:$target_id})
                RETURN EXISTS { MATCH (me)-[:FOLLOWS]->(target) } AS following
                """, me_id=current_user.id, target_id=user["user_id"]).single()
            is_following = bool(check["following"]) if check else False
        posts_result = session.run("""
            MATCH (u:User {username:$username})-[:CREATED]->(p:Post)
            OPTIONAL MATCH (p)<-[:LIKES]-(liker:User)
            WITH p, count(DISTINCT liker) AS likes
            OPTIONAL MATCH (p)-[:HAS_COMMENT]->(c:Comment)
            RETURN p.post_id AS post_id, p.content AS content,
                   p.created_at AS created_at, likes,
                   count(DISTINCT c) AS comments
            ORDER BY p.created_at DESC
            """, username=username)
        posts = [r.data() for r in posts_result]
    return render_template("profile.html", user=user, posts=posts, is_following=is_following)

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
            session.run("MATCH (u:User {user_id:$user_id}) SET u.name=$name, u.bio=$bio",
                        user_id=current_user.id, name=name, bio=bio)
        flash("Profile updated.")
        return redirect(url_for("profile.my_profile"))
    with driver.session(database=DATABASE) as session:
        record = session.run("MATCH (u:User {user_id:$user_id}) RETURN u.name AS name,u.bio AS bio",
                             user_id=current_user.id).single()
    return render_template("edit_profile.html", user=record.data() if record else {"name":"","bio":""})

@profile_bp.route("/follow/<username>", methods=["POST"])
@login_required
def follow(username):
    if username == current_user.username:
        flash("You cannot follow yourself.")
        return redirect(url_for("profile.profile", username=username))
    with driver.session(database=DATABASE) as session:
        record = session.run("""
            MATCH (me:User {user_id:$me_id}), (target:User {username:$username})
            OPTIONAL MATCH (me)-[existing:FOLLOWS]->(target)
            WITH me,target,existing
            FOREACH (_ IN CASE WHEN existing IS NULL THEN [1] ELSE [] END |
                CREATE (me)-[:FOLLOWS]->(target))
            RETURN target.user_id AS target_id, existing IS NULL AS created
            """, me_id=current_user.id, username=username).single()
        if not record:
            flash("User not found.")
            return redirect(url_for("posts.feed"))
        if record["created"]:
            create_notification(session, record["target_id"], current_user.id,
                               "follow", f"{current_user.username} started following you")
    flash("You are now following @"+username)
    return redirect(url_for("profile.profile", username=username))

@profile_bp.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):
    with driver.session(database=DATABASE) as session:
        session.run("""
            MATCH (me:User {user_id:$me_id})-[r:FOLLOWS]->(target:User {username:$username})
            DELETE r
            """, me_id=current_user.id, username=username)
    flash("You unfollowed @"+username)
    return redirect(url_for("profile.profile", username=username))
