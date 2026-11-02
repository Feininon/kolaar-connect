
from flask import Blueprint, render_template, request
from flask_login import login_required
from database.neo4j_connection import driver, DATABASE

hashtags_bp = Blueprint("hashtags", __name__)


@hashtags_bp.route("/hashtag/<tag>")
@login_required
def hashtag_posts(tag):
    tag = tag.lower().lstrip("#")

    with driver.session(database=DATABASE) as session:
        result = session.run(
            """
            MATCH (p:Post)-[:HAS_TAG]->(:Hashtag {name: $tag})
            MATCH (u:User)-[:CREATED]->(p)
            OPTIONAL MATCH (p)<-[:LIKES]-(liker:User)
            WITH p, u, count(DISTINCT liker) AS likes
            OPTIONAL MATCH (p)-[:HAS_COMMENT]->(c:Comment)
            RETURN p.post_id AS post_id,
                   p.content AS content,
                   u.username AS username,
                   likes,
                   count(DISTINCT c) AS comments,
                   p.created_at AS created_at
            ORDER BY created_at DESC
            """,
            tag=tag
        )

        posts = [record.data() for record in result]

    return render_template("hashtags.html", tag=tag, posts=posts)


@hashtags_bp.route("/hashtags/trending")
@login_required
def trending_hashtags():
    with driver.session(database=DATABASE) as session:
        result = session.run(
            """
            MATCH (p:Post)-[:HAS_TAG]->(h:Hashtag)
            RETURN h.name AS hashtag,
                   count(DISTINCT p) AS posts
            ORDER BY posts DESC
            LIMIT 20
            """
        )

        hashtags = [record.data() for record in result]

    return render_template("hashtags.html", hashtags=hashtags,
                           tag=None, posts=[])


@hashtags_bp.route("/hashtags/search")
@login_required
def search_hashtags():
    search_term = request.args.get("q", "").strip().lower().lstrip("#")

    hashtags = []

    if search_term:
        with driver.session(database=DATABASE) as session:
            result = session.run(
                """
                MATCH (h:Hashtag)
                WHERE h.name CONTAINS $search_term
                RETURN h.name AS hashtag
                ORDER BY h.name
                LIMIT 20
                """,
                search_term=search_term
            )

            hashtags = [record.data() for record in result]

    return render_template(
        "hashtags.html",
        hashtags=hashtags,
        tag=None,
        posts=[]
    )

