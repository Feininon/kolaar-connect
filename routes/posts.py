from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from database.neo4j_connection import driver, DATABASE
from routes.notifications import create_notification
import uuid, re

posts_bp = Blueprint("posts", __name__)

@posts_bp.route("/post/create", methods=["POST"])
@login_required
def create_post():
    content = request.form.get("content", "").strip()
    if not content:
        flash("Post cannot be empty.")
        return redirect(url_for("posts.feed"))
    post_id = str(uuid.uuid4())
    hashtags = sorted(set(t.lower() for t in re.findall(r"(?<!\w)#(\w+)", content)))
    with driver.session(database=DATABASE) as session:
        session.run("""
            MATCH (u:User {user_id:$user_id})
            CREATE (p:Post {post_id:$post_id,content:$content,created_at:datetime()})
            CREATE (u)-[:CREATED]->(p)
            """, user_id=current_user.id, post_id=post_id, content=content)
        if hashtags:
            session.run("""
                MATCH (p:Post {post_id:$post_id})
                UNWIND $hashtags AS tag
                MERGE (h:Hashtag {name:tag})
                MERGE (p)-[:HAS_TAG]->(h)
                """, post_id=post_id, hashtags=hashtags)
    flash("Post published.")
    return redirect(url_for("posts.feed"))

@posts_bp.route("/feed")
@login_required
def feed():
    with driver.session(database=DATABASE) as session:
        result = session.run("""
            MATCH (author:User)-[:CREATED]->(p:Post)
            OPTIONAL MATCH (viewer:User {user_id:$user_id})-[:LIKES]->(p)
            WITH author,p,count(viewer)>0 AS liked
            OPTIONAL MATCH (liker:User)-[:LIKES]->(p)
            WITH author,p,liked,count(DISTINCT liker) AS likes
            OPTIONAL MATCH (p)-[:HAS_COMMENT]->(c:Comment)
            WITH author,p,liked,likes,count(DISTINCT c) AS comments
            OPTIONAL MATCH (p)-[:HAS_COMMENT]->(comment:Comment)<-[:WROTE]-(commenter:User)
            WITH author,p,liked,likes,comments,
                 collect(CASE WHEN comment IS NULL THEN null ELSE
                   {content:comment.content,username:commenter.username} END) AS comment_list
            RETURN p.post_id AS post_id,p.content AS content,p.created_at AS created_at,
                   author.user_id AS author_id,author.username AS username,author.name AS name,
                   liked,likes,comments,comment_list
            ORDER BY p.created_at DESC
            """, user_id=current_user.id)
        posts = [r.data() for r in result]
        for post in posts:
            post["comment_list"] = [c for c in (post["comment_list"] or []) if c]
    return render_template("feed.html", posts=posts)

@posts_bp.route("/post/<post_id>/like", methods=["POST"])
@login_required
def like_post(post_id):
    with driver.session(database=DATABASE) as session:
        record = session.run("""
            MATCH (u:User {user_id:$user_id}), (p:Post {post_id:$post_id})
            OPTIONAL MATCH (u)-[existing:LIKES]->(p)
            WITH u,p,existing
            FOREACH (_ IN CASE WHEN existing IS NULL THEN [1] ELSE [] END |
                CREATE (u)-[:LIKES]->(p))
            OPTIONAL MATCH (owner:User)-[:CREATED]->(p)
            RETURN existing IS NULL AS created,owner.user_id AS owner_id
            """, user_id=current_user.id, post_id=post_id).single()
        if record and record["created"]:
            create_notification(session, record["owner_id"], current_user.id,
                               "like", f"{current_user.username} liked your post", post_id)
    return redirect(url_for("posts.feed"))

@posts_bp.route("/post/<post_id>/unlike", methods=["POST"])
@login_required
def unlike_post(post_id):
    with driver.session(database=DATABASE) as session:
        session.run("""
            MATCH (u:User {user_id:$user_id})-[r:LIKES]->(p:Post {post_id:$post_id})
            DELETE r
            """, user_id=current_user.id, post_id=post_id)
    return redirect(url_for("posts.feed"))

@posts_bp.route("/post/<post_id>/comment", methods=["POST"])
@login_required
def comment_post(post_id):
    content = request.form.get("content", "").strip()
    if not content:
        flash("Comment cannot be empty.")
        return redirect(url_for("posts.feed"))
    comment_id = str(uuid.uuid4())
    with driver.session(database=DATABASE) as session:
        record = session.run("""
            MATCH (u:User {user_id:$user_id}), (p:Post {post_id:$post_id})
            MATCH (owner:User)-[:CREATED]->(p)
            CREATE (c:Comment {comment_id:$comment_id,content:$content,created_at:datetime()})
            CREATE (u)-[:WROTE]->(c)
            CREATE (p)-[:HAS_COMMENT]->(c)
            RETURN owner.user_id AS owner_id
            """, user_id=current_user.id, post_id=post_id,
            comment_id=comment_id, content=content).single()
        if record:
            create_notification(session, record["owner_id"], current_user.id,
                               "comment", f"{current_user.username} commented on your post", post_id)
    flash("Comment added.")
    return redirect(url_for("posts.feed"))

@posts_bp.route("/post/<post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    with driver.session(database=DATABASE) as session:
        session.run("""
            MATCH (u:User {user_id:$user_id})-[:CREATED]->(p:Post {post_id:$post_id})
            OPTIONAL MATCH (p)-[:HAS_COMMENT]->(c:Comment)
            WITH p,collect(c) AS comments
            FOREACH (comment IN comments | DETACH DELETE comment)
            DETACH DELETE p
            """, user_id=current_user.id, post_id=post_id)
    flash("Post deleted.")
    return redirect(url_for("posts.feed"))
