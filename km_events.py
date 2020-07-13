import datetime
import db_helpers


class Event:
    def __init__(self, email, event_type, timestamp):
        self.email = email
        self.event_type = event_type
        self.timestamp = timestamp


def create_event(db, email, event_type):
    event_timestamp = datetime.datetime.utcnow().isoformat()
    # put together the query
    q_str = db_helpers.insert_into_string(
        TABLE_NAME,
        [FIELD_EMAIL, FIELD_EVENTTYPE, FIELD_TIMESTAMP])
    c = db.cursor()
    c.execute(q_str, [email, event_type, event_timestamp])
    db.commit()


########
# Defs #
########
TABLE_NAME = 'km_events'
FIELD_EVENTID = 'event_id'
FIELD_EMAIL = 'email'
FIELD_EVENTTYPE = 'event_type'
FIELD_TIMESTAMP = 'event_timestamp'
