
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from database.neo4j_connection import driver, DATABASE

graph_bp = Blueprint("graph", __name__)


@graph_bp.route("/graph")
@login_required
def social_graph():
    return render_template("graph.html")


@graph_bp.route("/api/graph")
@login_required
def graph_data():
    with driver.session(database=DATABASE) as session:
        result = session.run(
            """
            MATCH (me:User {user_id: $user_id})
            OPTIONAL MATCH (me)-[:FOLLOWS]->(u:User)
            WITH me, collect(DISTINCT u) AS following
            WITH [me] + [u IN following WHERE u IS NOT NULL] AS users
            UNWIND users AS user
            OPTIONAL MATCH (user)-[r:FOLLOWS]->(target:User)
            WHERE target IN users
            RETURN user, target
            """,
            user_id=current_user.id
        )

        nodes = {}
        edges = []

        for record in result:
            user = record["user"]
            target = record["target"]

            nodes[user["user_id"]] = {
                "data": {
                    "id": user["user_id"],
                    "label": user["username"],
                    "username": user["username"]
                }
            }

            if target:
                nodes[target["user_id"]] = {
                    "data": {
                        "id": target["user_id"],
                        "label": target["username"],
                        "username": target["username"]
                    }
                }

                edges.append({
                    "data": {
                        "source": user["user_id"],
                        "target": target["user_id"]
                    }
                })

    return jsonify({
        "nodes": list(nodes.values()),
        "edges": edges
    })
