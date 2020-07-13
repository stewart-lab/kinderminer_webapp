from multiprocessing import Pool
from postmarker.core import PostmarkClient

import json
import time
import secret
import km_users
import km_requests
import pymysql.cursors
import chtc_query
import getFET

#################
# Parse Helpers #
#################


def to_bool(val):
    return str(val).lower() in {'true', 't', '1', 'yes', 'y'}


def try_parse_int(val):
    if isinstance(val, int):
        return val
    try:
        return int(val)
    except ValueError:
        return None

#################
# Email Helpers #
#################


def send_email(from_addr, to_addr, subject, body, api_token):
    postmark_client = PostmarkClient(server_token=api_token)
    postmark_client.emails.send(
        From=from_addr,
        To=to_addr,
        Subject=subject,
        HtmlBody=body)


def send_request_complete_email(to_addr, request_name):
    # gather our data
    from_addr = 'kinderminer@morgridge.org'
    subject = 'KinderMiner Query Complete'
    km_link = 'https://www.kinderminer.org'
    # TODO this should probably be a rendered template instead
    body = 'Hi {0},<br>Your KinderMiner query [{1}] is complete. Please log in to view your results.<br><br>{2}'.format(
        to_addr, request_name, km_link)
    # send it
    send_email(from_addr, to_addr, subject, body, secret.email_api_token)

##############
# DB Helpers #
##############


def open_db_connection():
    # spin on connection until we have it
    db = None
    while db is None:
        try:
            db = pymysql.connect(
                host=secret.db_host,
                port=secret.db_port,
                database=secret.db_name,
                user=secret.db_user,
                password=secret.db_pass)
        except:
            print('failed connecting to DB - retrying')
            db = None
            time.sleep(5)
    return db


def reset_stuck_requests():
    # NOTE: this logic assumes there is only ever one analysis_daemon running
    #
    # on startup, requests that are in progress but not done are jobs that
    # will not be completed by a restart of the analysis daemon
    # if the analysis daemon crashes while in progress on a request, the child
    # process will not be able to complete the request and mark it as done yet
    # it will remain marked as 'in progress' so it will not be started again
    db = open_db_connection()
    reqs_to_reset = km_requests.select_all_in_progress_but_not_done(db)
    # go through and mark as not in progress
    for req in reqs_to_reset:
        print('resetting stuck request [{0}]'.format(req.name))
        km_requests.update_in_progress_by_id(db, req.req_id, False)
    # we are done here
    db.close()


############
# Analysis #
############


def process_request(request):
    # pull out the parameters for convenience
    # TODO handle any weirdness that snuck into the database?
    params = request.params
    target_terms = params['target_terms'].split('\n')
    key_phrase = params['key_phrase']
    censor_year = try_parse_int(params['censor_year'])
    sep_kp = to_bool(params['sep_kp'])
    # first we need to run the article count query
    counts_dict = chtc_query.api_full_query(
        target_terms, key_phrase, censor_year, sep_kp)
    # and then do statistical analysis
    results_dict = getFET.api_compute_fets(counts_dict)
    # get a database connection for updating
    db = open_db_connection()
    # store the results
    results_str = json.dumps(results_dict)
    km_requests.update_results_by_id(db, request.req_id, results_str)
    # set the complete time
    km_requests.update_complete_time_to_utc_now_by_id(db, request.req_id)
    # mark as done
    km_requests.update_done_by_id(db, request.req_id, True)
    # get the user account attached to this email
    user = km_users.get_one_by_email(db, request.email)
    # close the database now that we are done with it
    db.close()
    # and send an email to the owner if they are not a guest account
    if not (user is None or user.is_guest):
        send_request_complete_email(request.email, request.name)

########
# Main #
########


N_PROCESSES = 4


def main():
    # first we will look for jobs that are stuck due to early termination of
    # this daemon on the last run
    # NOTE: the logic of this assumes that only one daemon ever runs
    reset_stuck_requests()
    # we will process requests in a multi-threaded fashion
    pool = Pool(processes=N_PROCESSES)
    # just run forever for now
    # TODO this should be smarter to handle unexpected termination
    done = False
    while not done:
        # get a connection
        db = open_db_connection()
        # grab all requests not in progress already
        reqs_to_process = km_requests.select_all_not_in_progress(db)
        # go through each
        for req in reqs_to_process:
            print('handling request [{0}]'.format(req.name))
            # mark it as in progress
            km_requests.update_in_progress_by_id(db, req.req_id, True)
            # and queue it up for execution
            pool.apply_async(process_request, [req])
        # close our connection
        db.close()
        # and take a little nap
        time.sleep(5)
    # close the pool when done
    pool.close()


if __name__ == '__main__':
    main()
