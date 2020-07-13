import json
import datetime
import db_helpers


class Request:
    def __init__(
            self,
            req_id,
            email,
            name,
            params,
            results,
            submit_time,
            complete_time,
            in_progress,
            done):
        self.req_id = req_id
        self.email = email
        self.name = name
        # handle weird params and results since we're loading json
        if params is None or len(params) < 1:
            params = '{}'
        self.params = json.loads(params)
        if results is None or len(results) < 1:
            results = '{}'
        self.results = json.loads(results)
        # handle weird datetime input since we're loading strings
        if submit_time is None or len(submit_time) < 1:
            submit_time = DATE_DMY.isoformat()
        self.submit_time = datetime.datetime.fromisoformat(submit_time)
        if complete_time is None or len(complete_time) < 1:
            complete_time = DATE_DMY.isoformat()
        self.complete_time = datetime.datetime.fromisoformat(complete_time)
        # load these as booleans
        self.in_progress = to_bool(in_progress)
        self.done = to_bool(done)


def to_bool(val):
    return str(val).lower() in {'true', 't', '1', 'yes', 'y'}


def submit_request(db, email, name, params_dict):
    print('hit submit_request')
    # no nulls
    if email is None or name is None or params_dict is None:
        print('None in submit_request {0}'.format([email, name, params_dict]))
        return
    # generate a full insert string
    q_str = db_helpers.insert_into_string(TABLE_NAME, ORDERED_FIELDS_NO_ID)
    # need to dump params to json for storage
    params = json.dumps(params_dict)
    # and results are empty for now
    results = json.dumps({})
    # submit time is right now
    submit_time = datetime.datetime.utcnow().isoformat()
    # complete time hasn't happened
    complete_time = DATE_DMY.isoformat()
    # not in progress and not done
    in_progress = False
    done = False
    # let's do this
    vals = [
        email,
        name,
        params,
        results,
        submit_time,
        complete_time,
        in_progress,
        done]
    c = db.cursor()
    c.execute(q_str, vals)
    db.commit()


def select_all(db):
    # generate the full select string for the constructor
    q_str = db_helpers.select_string(TABLE_NAME, CONSTRUCTOR_FIELDS)
    # and select
    c = db.cursor()
    c.execute(q_str)
    reqs = [
        Request(
            r[0],
            r[1],
            r[2],
            r[3],
            r[4],
            r[5],
            r[6],
            r[7],
            r[8]) for r in c.fetchall()]
    return reqs


def select_by_email(db, email):
    # no nulls
    if email is None:
        return None
    # generate the full select with where for the constructor
    q_str = db_helpers.select_where_string(
        TABLE_NAME, CONSTRUCTOR_FIELDS, FIELD_EMAIL)
    # and select
    c = db.cursor()
    c.execute(q_str, [email])
    reqs = [
        Request(
            r[0],
            r[1],
            r[2],
            r[3],
            r[4],
            r[5],
            r[6],
            r[7],
            r[8]) for r in c.fetchall()]
    return reqs


def select_all_not_in_progress(db):
    # we want requests not in progress
    in_progress = False
    # generate the full select with where for the constructor
    q_str = db_helpers.select_where_string(
        TABLE_NAME, CONSTRUCTOR_FIELDS, FIELD_INPROGRESS)
    # and select
    c = db.cursor()
    c.execute(q_str, [in_progress])
    reqs = [
        Request(
            r[0],
            r[1],
            r[2],
            r[3],
            r[4],
            r[5],
            r[6],
            r[7],
            r[8]) for r in c.fetchall()]
    return reqs


def select_all_in_progress_but_not_done(db):
    # we want requests that are in progress, but not done yet
    in_progress = True
    done = False
    # generate the full select with where for the constructor
    where_fields = [FIELD_INPROGRESS, FIELD_DONE]
    q_str = db_helpers.select_multiwhere_string(
        TABLE_NAME, CONSTRUCTOR_FIELDS, where_fields)
    # and select
    c = db.cursor()
    c.execute(q_str, [in_progress, done])
    reqs = [
        Request(
            r[0],
            r[1],
            r[2],
            r[3],
            r[4],
            r[5],
            r[6],
            r[7],
            r[8]) for r in c.fetchall()]
    return reqs


def select_one_by_id(db, req_id):
    # no nulls
    if req_id is None:
        return None
    # generate the full select with where for the constructor
    q_str = db_helpers.select_where_string(
        TABLE_NAME, CONSTRUCTOR_FIELDS, FIELD_REQUESTID)
    # and select
    c = db.cursor()
    c.execute(q_str, [req_id])
    reqs = [
        Request(
            r[0],
            r[1],
            r[2],
            r[3],
            r[4],
            r[5],
            r[6],
            r[7],
            r[8]) for r in c.fetchall()]
    # there should only be one
    if len(reqs) < 1:
        return None
    return reqs[0]


def update_in_progress_by_id(db, req_id, in_progress):
    # generate an update string on the in progress field with id as where
    q_str = db_helpers.update_where_string(
        TABLE_NAME, FIELD_INPROGRESS, FIELD_REQUESTID)
    # and execute it
    c = db.cursor()
    c.execute(q_str, [in_progress, req_id])
    db.commit()


def update_done_by_id(db, req_id, done):
    # generate an update string on the done field with id as where
    q_str = db_helpers.update_where_string(
        TABLE_NAME, FIELD_DONE, FIELD_REQUESTID)
    # and execute it
    c = db.cursor()
    c.execute(q_str, [done, req_id])
    db.commit()


def update_complete_time_to_utc_now_by_id(db, req_id):
    # generate an update string on the complete time field with id as where
    q_str = db_helpers.update_where_string(
        TABLE_NAME, FIELD_COMPLETETIME, FIELD_REQUESTID)
    # get the current time in UTC
    complete_time = datetime.datetime.utcnow().isoformat()
    # and execute it
    c = db.cursor()
    c.execute(q_str, [complete_time, req_id])
    db.commit()


def update_results_by_id(db, req_id, results):
    # generate an update string on the results field with id as where
    q_str = db_helpers.update_where_string(
        TABLE_NAME, FIELD_RESULTS, FIELD_REQUESTID)
    # and execute it
    c = db.cursor()
    c.execute(q_str, [results, req_id])
    db.commit()


def delete_by_id(db, req_id):
    # no nulls
    if req_id is None:
        return
    # generate the delete string with the id field
    q_str = db_helpers.delete_where_string(TABLE_NAME, FIELD_REQUESTID)
    # and delete
    c = db.cursor()
    c.execute(q_str, [req_id])
    db.commit()


def try_select_by_id_if_email_match(db, req_id, email):
    # don't bother with nulls
    if req_id is None or email is None:
        return None
    # otherwise, try to get the specified request
    req = select_one_by_id(db, req_id)
    if req is None:
        return None
    # and finally check the email for a match
    if req.email != email:
        return None
    return req

##############
# Table Defs #
##############


TABLE_NAME = 'km_requests'
FIELD_REQUESTID = 'request_id'
FIELD_EMAIL = 'email'
FIELD_REQUESTNAME = 'request_name'
FIELD_PARAMS = 'params'
FIELD_RESULTS = 'results'
FIELD_SUBMITTIME = 'submit_time'
FIELD_COMPLETETIME = 'complete_time'
FIELD_INPROGRESS = 'in_progress'
FIELD_DONE = 'done'

# for generating full insert/selects
CONSTRUCTOR_FIELDS = [
    FIELD_REQUESTID,
    FIELD_EMAIL,
    FIELD_REQUESTNAME,
    FIELD_PARAMS,
    FIELD_RESULTS,
    FIELD_SUBMITTIME,
    FIELD_COMPLETETIME,
    FIELD_INPROGRESS,
    FIELD_DONE]
ORDERED_FIELDS_NO_ID = [
    FIELD_EMAIL,
    FIELD_REQUESTNAME,
    FIELD_PARAMS,
    FIELD_RESULTS,
    FIELD_SUBMITTIME,
    FIELD_COMPLETETIME,
    FIELD_INPROGRESS,
    FIELD_DONE]

# for storing and retrieving date strings
DATE_DMY = datetime.datetime(1901, 1, 1)
