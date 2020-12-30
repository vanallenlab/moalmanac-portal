from flask_login import UserMixin

from app.db import get_db
from app.dict_manager import DateTime


class User(UserMixin):
    def __init__(self, unique_id,
                 email, display, registered, billable, ready,
                 access_token, refresh_token, scopes, time_authorized, time_authorized_original):
        self.id = unique_id
        self.email = email
        self.display = display
        self.registered = registered
        self.billable = billable
        self.ready = ready
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.scopes = scopes
        self.time_authorized = time_authorized
        self.time_authorized_original = time_authorized_original

    @classmethod
    def create(cls, unique_id, email, registered, billable, access_token, refresh_token, scopes):
        db = get_db()

        display = email.split('@')[0]
        ready = cls.evaluate_instructions(registered, billable)

        scopes_str = ' '.join(scopes)
        time_authorized = DateTime.datetime_for_session()
        time_authorized_original = time_authorized

        sql = "INSERT INTO user " \
              "(id, email, display, registered, billable, ready, access_token, refresh_token, scopes, " \
              "time_authorized, time_authorized_original) " \
              "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

        db.execute(sql, (unique_id,
                         email, display, registered, billable, ready, access_token, refresh_token, scopes_str,
                         time_authorized, time_authorized_original))
        db.commit()

    @staticmethod
    def evaluate_instructions(registered, billable):
        if registered == 200 and billable == 200:
            return True
        else:
            return False

    @staticmethod
    def get(unique_id):
        db = get_db()

        query = "SELECT * FROM user WHERE id = ?"
        user = db.execute(query, (unique_id,)).fetchone()
        if not user:
            return None

        user = User(unique_id=user[0],
                    email=user[1],
                    display=user[2],
                    registered=user[3],
                    billable=user[4],
                    ready=user[5],
                    access_token=user[6],
                    refresh_token=user[7],
                    scopes=user[8],
                    time_authorized=user[9],
                    time_authorized_original=user[10]
                    )
        return user

    @staticmethod
    def update_status(unique_id, registered, billable):
        db = get_db()
        sql = "UPDATE user SET registered = ?, billable = ? WHERE id = ?"
        db.execute(sql, (registered, billable, unique_id))
        db.commit()

    @staticmethod
    def update_tokens(unique_id, access_token, refresh_token, scopes):
        db = get_db()
        scopes_str = ' '.join(scopes)
        sql = "UPDATE user SET access_token = ?, refresh_token = ?, scopes = ? WHERE id = ?"
        db.execute(sql, (access_token, refresh_token, scopes_str, unique_id))
        db.commit()

