import db_helpers


class Session:
    def __init__(self, email, token):
        self.email = email
        self.token = token


def create_session_token(db, email, token):
    c = db.cursor()
    q_str = db_helpers.insert_into_string(
        TABLE_NAME, [FIELD_EMAIL, FIELD_TOKEN])
    c.execute(q_str, [email, token])
    db.commit()


def get_one_by_email(db, email):
    if email is None:
        return None
    q_str = db_helpers.select_where_string(
        TABLE_NAME, [FIELD_EMAIL, FIELD_TOKEN], FIELD_EMAIL)
    c = db.cursor()
    c.execute(q_str, [email])
    user_sessions = [Session(r[0], r[1]) for r in c.fetchall()]
    if len(user_sessions) < 1:
        return None
    return user_sessions[0]


def delete_by_email(db, email):
    c = db.cursor()
    q_str = db_helpers.delete_where_string(TABLE_NAME, FIELD_EMAIL)
    c.execute(q_str, [email])
    db.commit()


########
# Defs #
########
TABLE_NAME = 'km_user_sessions'
FIELD_USERSESSIONID = 'user_session_id'
FIELD_EMAIL = 'email'
FIELD_TOKEN = 'token'
