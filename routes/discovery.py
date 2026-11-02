
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from database.neo4j_connection import driver, DATABASE

discovery_bp = Blueprint("discovery", __name__)


@discovery_bp.route("/search")
@login_required
def search_users():
    query = request.args.get("q", "").strip()

    users = []

    if query:
        with driver.session(database=DATABASE) as session:
            result = session.run(
                """
                MATCH (u:User)
                WHERE (
                    toLower(u.username) CONTAINS toLower($q)
                    OR toLower(u.name) CONTAINS toLower($q)
                )
                AND u.user_id <> $user_id
                RETURN u.user_id AS user_id,
                       u.username AS username,
                       u.name AS name
                ORDER BY u.username
                LIMIT 20
                """,
                q=query,
                user_id=current_user.id
            )
            users = [record.data() for record in result]

    return render_template("discovery.html", users=users,
                           recommendations=[], mutuals=[],
                           query=query, target=None)


@discovery_bp.route("/recommendations")
@login_required
def recommendations():
    with driver.session(database=DATABASE) as session:
        result = session.run(
            """
            MATCH (me:User {user_id: $user_id})-[:FOLLOWS]->(friend:User)
                  -[:FOLLOWS]->(recommended:User)
            WHERE recommended.user_id <> $user_id
              AND NOT (me)-[:FOLLOWS]->(recommended)
            WITH recommended, count(DISTINCT friend) AS common
            RETURN recommended.username AS username,
                   recommended.name AS name,
                   common
            ORDER BY common DESC
            LIMIT 20
            """,
            user_id=current_user.id
        )

        recommendations = [record.data() for record in result]

    return render_template(
        "discovery.html",
        users=[],
        recommendations=recommendations,
        mutuals=[],
        query="",
        target=None
    )


@discovery_bp.route("/mutual/<username>")
@login_required
def mutual_connections(username):
    with driver.session(database=DATABASE) as session:
        result = session.run(
            """
            MATCH (me:User {user_id: $user_id})
            MATCH (other:User {username: $username})
            MATCH (me)-[:FOLLOWS]->(mutual:User)
                  <-[:FOLLOWS]-(other)
            RETURN mutual.username AS username,
                   mutual.name AS name
            ORDER BY mutual.username
            """,
            user_id=current_user.id,
            username=username
        )

        mutuals = [record.data() for record in result]

    return render_template(
        "discovery.html",
        users=[],
        recommendations=[],
        mutuals=mutuals,
        query="",
        target=username
    )
