from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, user_id, username, email, name):
        self.id = user_id
        self.username = username
        self.email = email
        self.name = name