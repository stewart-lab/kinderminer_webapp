import db_helpers


class Reset:
    def __init__(self, token, email):
        self.token = token
        self.email = email


def insert_token(db, token, email):
    c = db.cursor()
    q_str = db_helpers.insert_into_string(
        TABLE_NAME, [FIELD_TOKEN, FIELD_EMAIL])
    c.execute(q_str, [token, email])
    db.commit()


def get_one_by_email(db, email):
    c = db.cursor()
    q_str = db_helpers.select_where_string(
        TABLE_NAME, [FIELD_TOKEN, FIELD_EMAIL], FIELD_EMAIL)
    c.execute(q_str, [email])
    resets = [Reset(r[0], r[1]) for r in c.fetchall()]
    if len(resets) < 1:
        return None
    return resets[0]


def get_one_by_token(db, token):
    c = db.cursor()
    q_str = db_helpers.select_where_string(
        TABLE_NAME, [FIELD_TOKEN, FIELD_EMAIL], FIELD_TOKEN)
    c.execute(q_str, [token])
    resets = [Reset(r[0], r[1]) for r in c.fetchall()]
    if len(resets) < 1:
        return None
    return resets[0]


def delete_by_email(db, email):
    c = db.cursor()
    q_str = db_helpers.delete_where_string(TABLE_NAME, FIELD_EMAIL)
    c.execute(q_str, [email])
    db.commit()


########
# Defs #
########
TABLE_NAME = 'km_reset_tokens'
FIELD_RESETTOKENID = 'reset_token_id'
FIELD_EMAIL = 'email'
FIELD_TOKEN = 'token'
