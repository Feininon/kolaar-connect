
import uuid
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from database.neo4j_connection import driver, DATABASE

posts_bp = Blueprint("posts", __name__)



@posts_bp.route("/post/create", methods=["POST"])
@login_required
def create_post():
    content = request.form.get("content", "").strip()

    if not content:
        flash("Post cannot be empty.")
        return redirect(url_for("posts.feed"))

    post_id = str(uuid.uuid4())

    # Extract hashtags, remove duplicates, normalize case
    hashtags = list(set(
        tag.lower()
        for tag in re.findall(r"(?<!\w)#(\w+)", content)
    ))

    with driver.session(database=DATABASE) as session:
        session.run(
            """
            MATCH (u:User {user_id: $user_id})
            CREATE (p:Post {
                post_id: $post_id,
                content: $content,
                created_at: datetime()
            })
            CREATE (u)-[:CREATED]->(p)

            WITH p
            UNWIND $hashtags AS tag
            MERGE (h:Hashtag {name: tag})
            MERGE (p)-[:HAS_TAG]->(h)
            """,
            user_id=current_user.id,
            post_id=post_id,
            content=content,
            hashtags=hashtags
        )

    return redirect(url_for("posts.feed"))


@posts_bp.route("/feed")
@login_required
def feed():
    with driver.session(database=DATABASE) as session:
        result = session.run(
            """
            MATCH (author:User)-[:CREATED]->(p:Post)
            WHERE author.user_id = $user_id
               OR EXISTS {
                   MATCH (:User {user_id: $user_id})
                         -[:FOLLOWS]->(author)
               }
            OPTIONAL MATCH (p)<-[:LIKES]-(liker:User)
            WITH author, p, count(DISTINCT liker) AS likes
            OPTIONAL MATCH (p)-[:HAS_COMMENT]->(c:Comment)
            WITH author, p, likes,
                 count(DISTINCT c) AS comments
            RETURN author.username AS username,
                   author.name AS name,
                   p.post_id AS post_id,
                   p.content AS content,
                   p.created_at AS created_at,
                   likes, comments
            ORDER BY created_at DESC
            """,
            user_id=current_user.id
        )

        posts = [record.data() for record in result]

    return render_template("feed.html", posts=posts)


@posts_bp.route("/post/<post_id>/like", methods=["POST"])
@login_required
def like_post(post_id):
    with driver.session(database=DATABASE) as session:
        session.run(
            """
            MATCH (u:User {user_id: $user_id})
            MATCH (p:Post {post_id: $post_id})
            MERGE (u)-[:LIKES]->(p)
            """,
            user_id=current_user.id,
            post_id=post_id
        )

    return redirect(url_for("posts.feed"))


@posts_bp.route("/post/<post_id>/unlike", methods=["POST"])
@login_required
def unlike_post(post_id):
    with driver.session(database=DATABASE) as session:
        session.run(
            """
            MATCH (u:User {user_id: $user_id})
                  -[r:LIKES]->
                  (p:Post {post_id: $post_id})
            DELETE r
            """,
            user_id=current_user.id,
            post_id=post_id
        )

    return redirect(url_for("posts.feed"))


@posts_bp.route("/post/<post_id>/comment", methods=["POST"])
@login_required
def comment_post(post_id):
    content = request.form.get("content", "").strip()

    if not content:
        return redirect(url_for("posts.feed"))

    comment_id = str(uuid.uuid4())

    with driver.session(database=DATABASE) as session:
        session.run(
            """
            MATCH (u:User {user_id: $user_id})
            MATCH (p:Post {post_id: $post_id})
            CREATE (c:Comment {
                comment_id: $comment_id,
                content: $content,
                created_at: datetime()
            })
            CREATE (u)-[:WROTE]->(c)
            CREATE (p)-[:HAS_COMMENT]->(c)
            """,
            user_id=current_user.id,
            post_id=post_id,
            comment_id=comment_id,
            content=content
        )

    return redirect(url_for("posts.feed"))


@posts_bp.route("/post/<post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    with driver.session(database=DATABASE) as session:
        session.run(
            """
            MATCH (u:User {user_id: $user_id})
                  -[:CREATED]->
                  (p:Post {post_id: $post_id})
            OPTIONAL MATCH (p)<-[:HAS_COMMENT]-(c:Comment)
            DETACH DELETE p, c
            """,
            user_id=current_user.id,
            post_id=post_id
        )

    return redirect(url_for("posts.feed"))
