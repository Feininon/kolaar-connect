
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from database.neo4j_connection import driver, DATABASE

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
@login_required
def analytics_home():
    return render_template("analytics.html")


@analytics_bp.route("/shortest-path", methods=["POST"])
@login_required
def shortest_path():
    target = request.form.get("username", "").strip()

    with driver.session(database=DATABASE) as session:
        result = session.run(
            """
            MATCH (me:User {user_id: $user_id})
            MATCH (target:User {username: $target})
            MATCH path = shortestPath(
                (me)-[:FOLLOWS*0..10]-(target)
            )
            RETURN [node IN nodes(path) | node.username] AS path
            """,
            user_id=current_user.id,
            target=target
        ).single()

    path = result["path"] if result else None

    return render_template(
        "analytics.html",
        path=path,
        target=target,
        pagerank=None,
        centrality=None,
        trending=None
    )


@analytics_bp.route("/degree-centrality")
@login_required
def degree_centrality():
    with driver.session(database=DATABASE) as session:
        result = session.run(
            """
            MATCH (u:User)
            OPTIONAL MATCH (u)-[:FOLLOWS]-(connected:User)
            RETURN u.username AS username,
                   count(DISTINCT connected) AS connections
            ORDER BY connections DESC
            LIMIT 20
            """
        )

        centrality = [record.data() for record in result]

    return render_template(
        "analytics.html",
        centrality=centrality,
        path=None,
        target=None,
        pagerank=None,
        trending=None
    )


@analytics_bp.route("/trending")
@login_required
def trending_posts():
    with driver.session(database=DATABASE) as session:
        result = session.run(
            """
            MATCH (u:User)-[:CREATED]->(p:Post)
            OPTIONAL MATCH (p)<-[:LIKES]-(liker:User)
            WITH u, p, count(DISTINCT liker) AS likes
            OPTIONAL MATCH (p)-[:HAS_COMMENT]->(c:Comment)
            WITH u, p, likes, count(DISTINCT c) AS comments
            RETURN p.post_id AS post_id,
                   p.content AS content,
                   u.username AS username,
                   likes,
                   comments,
                   (likes * 2 + comments) AS score
            ORDER BY score DESC
            LIMIT 20
            """
        )

        trending = [record.data() for record in result]

    return render_template(
        "analytics.html",
        trending=trending,
        path=None,
        target=None,
        pagerank=None,
        centrality=None
    )

@analytics_bp.route("/pagerank")
@login_required
def pagerank():
    with driver.session(database=DATABASE) as session:
        result = session.run(
            """
            CALL gds.pageRank.stream('kolaar-social')
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).username AS username,
                   score
            ORDER BY score DESC
            LIMIT 20
            """
        )

        pagerank = [record.data() for record in result]

    return render_template(
        "analytics.html",
        pagerank=pagerank,
        path=None,
        target=None,
        centrality=None,
        trending=None
    )