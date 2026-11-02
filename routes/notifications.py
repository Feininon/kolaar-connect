
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from database.neo4j_connection import driver, DATABASE
import uuid

notifications_bp = Blueprint("notifications", __name__)


def create_notification(
    session,
    recipient_id,
    actor_id,
    notification_type,
    message,
    post_id=None
):
    if not recipient_id or recipient_id == actor_id:
        return

    notification_id = str(uuid.uuid4())

    session.run(
        """
        MATCH (recipient:User {user_id: $recipient_id})
        MATCH (actor:User {user_id: $actor_id})

        CREATE (n:Notification {
            notification_id: $notification_id,
            type: $notification_type,
            message: $message,
            read: false,
            created_at: datetime()
        })

        CREATE (recipient)-[:RECEIVED]->(n)
        CREATE (n)-[:FROM]->(actor)

        WITH n
        OPTIONAL MATCH (p:Post {post_id: $post_id})
        FOREACH (_ IN CASE WHEN p IS NOT NULL THEN [1] ELSE [] END |
            CREATE (n)-[:ABOUT]->(p)
        )
        """,
        recipient_id=recipient_id,
        actor_id=actor_id,
        notification_id=notification_id,
        notification_type=notification_type,
        message=message,
        post_id=post_id
    )


@notifications_bp.route("/notifications")
@login_required
def notifications():

    with driver.session(database=DATABASE) as session:

        result = session.run(
            """
            MATCH (u:User {user_id: $user_id})-[:RECEIVED]->(n:Notification)
            OPTIONAL MATCH (n)-[:FROM]->(actor:User)
            OPTIONAL MATCH (n)-[:ABOUT]->(p:Post)

            RETURN
                n.notification_id AS notification_id,
                n.type AS type,
                n.message AS message,
                n.read AS read,
                n.created_at AS created_at,
                actor.username AS actor_username,
                p.post_id AS post_id

            ORDER BY n.created_at DESC
            LIMIT 100
            """,
            user_id=current_user.id
        )

        notifications_list = [record.data() for record in result]

        unread_result = session.run(
            """
            MATCH (u:User {user_id: $user_id})-[:RECEIVED]->(n:Notification)
            WHERE n.read = false
            RETURN count(n) AS unread_count
            """,
            user_id=current_user.id
        )

        unread_count = unread_result.single()["unread_count"]

    return render_template(
        "notifications.html",
        notifications=notifications_list,
        unread_count=unread_count
    )


@notifications_bp.route(
    "/notifications/read/<notification_id>",
    methods=["POST"]
)
@login_required
def mark_notification_read(notification_id):

    with driver.session(database=DATABASE) as session:
        session.run(
            """
            MATCH (u:User {user_id: $user_id})-[:RECEIVED]->(n:Notification {
                notification_id: $notification_id
            })
            SET n.read = true
            """,
            user_id=current_user.id,
            notification_id=notification_id
        )

    return redirect(url_for("notifications.notifications"))


@notifications_bp.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_notifications_read():

    with driver.session(database=DATABASE) as session:
        session.run(
            """
            MATCH (u:User {user_id: $user_id})-[:RECEIVED]->(n:Notification)
            SET n.read = true
            """,
            user_id=current_user.id
        )

    return redirect(url_for("notifications.notifications"))
