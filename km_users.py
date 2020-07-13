import datetime
import db_helpers


class User:
    def __init__(self, email, pass_hash, is_guest):
        self.email = email
        self.pass_hash = pass_hash
        self.is_guest = to_bool(is_guest)


def to_bool(val):
    return str(val).lower() in {'true', 't', '1', 'yes', 'y'}


def create_user_account(db, email, pass_hash):
    create_time = datetime.datetime.utcnow().isoformat()
    last_login = create_time
    q_str = db_helpers.insert_into_string(
        TABLE_NAME,
        [FIELD_EMAIL, FIELD_PASSHASH, FIELD_CREATETIME, FIELD_LASTLOGIN])
    c = db.cursor()
    c.execute(q_str, [email, pass_hash, create_time, last_login])
    db.commit()
    return get_one_by_email(db, email)


def create_guest_user_account(db, email, pass_hash):
    # start with a standard creation
    user = create_user_account(db, email, pass_hash)
    # and mark the account as a guest
    q_str = db_helpers.update_where_string(
        TABLE_NAME, FIELD_GUESTACCOUNT, FIELD_EMAIL)
    c = db.cursor()
    c.execute(q_str, [True, email])
    db.commit()
    return get_one_by_email(db, email)


def get_one_by_email(db, email):
    if email is None:
        return None
    q_str = db_helpers.select_where_string(
        TABLE_NAME, [FIELD_EMAIL, FIELD_PASSHASH, FIELD_GUESTACCOUNT], FIELD_EMAIL)
    c = db.cursor()
    c.execute(q_str, [email])
    users = [User(r[0], r[1], r[2]) for r in c.fetchall()]
    if len(users) < 1:
        return None
    return users[0]


def is_email_already_taken(db, email):
    user = get_one_by_email(db, email)
    if user is None:
        return False
    return True


def reset_pass_hash(db, email, pass_hash):
    if email is None:
        return None
    q_str = db_helpers.update_where_string(
        TABLE_NAME, FIELD_PASSHASH, FIELD_EMAIL)
    c = db.cursor()
    c.execute(q_str, [pass_hash, email])
    db.commit()


def update_last_login(db, email):
    if email is None:
        return None
    last_login = datetime.datetime.utcnow().isoformat()
    q_str = db_helpers.update_where_string(
        TABLE_NAME, FIELD_LASTLOGIN, FIELD_EMAIL)
    c = db.cursor()
    c.execute(q_str, [last_login, email])
    db.commit()


########
# Defs #
########
TABLE_NAME = 'km_users'
FIELD_USERID = 'user_id'
FIELD_EMAIL = 'email'
FIELD_PASSHASH = 'password_hash'
FIELD_CREATETIME = 'create_time'
FIELD_LASTLOGIN = 'last_login'
FIELD_GUESTACCOUNT = 'guest_account'
