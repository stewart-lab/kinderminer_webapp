from flask import (Flask, redirect, render_template, request, session, Response,
                   jsonify, g, send_from_directory, url_for)
from flaskext.mysql import MySQL
from postmarker.core import PostmarkClient
import os
import bcrypt
import datetime
import secret
import km_users
import km_user_sessions
import km_reset_tokens
import km_requests
import km_events
import csv

mysql = MySQL()
app = Flask(__name__)
app.config['MYSQL_DATABASE_USER'] = secret.db_user
app.config['MYSQL_DATABASE_PASSWORD'] = secret.db_pass
app.config['MYSQL_DATABASE_DB'] = secret.db_name
app.config['MYSQL_DATABASE_HOST'] = secret.db_host
app.config['MYSQL_DATABASE_PORT'] = secret.db_port
mysql.init_app(app)

#################
# Parse Helpers #
#################


def try_parse_int(val):
    if isinstance(val, int):
        return val
    try:
        return int(val)
    except:
        return None


def try_parse_float(val):
    if isinstance(val, float):
        return val
    try:
        return float(val)
    except:
        return None


def to_bool(val):
    return str(val).lower() in {'true', 't', '1', 'yes', 'y'}


######################
# User Login Helpers #
######################


SESSION_TOKEN_KEY = secret.session_token_key
SESSION_EMAIL_KEY = secret.session_email_key


def logged_in():
    user = get_logged_in_user()
    return user is not None


def get_logged_in_user():
    token = session.get(SESSION_TOKEN_KEY)
    email = session.get(SESSION_EMAIL_KEY)
    if email is not None and token is not None:
        user = km_user_sessions.get_one_by_email(g.db, email)
        if user.token != token:
            return None
        else:
            return user
    return None


def logout_user(email):
    if email is None:
        return
    # clear any session tokens from the sessions table
    km_user_sessions.delete_by_email(g.db, email)
    # and clear token info from the session cookie
    session.pop(SESSION_TOKEN_KEY, None)
    session.pop(SESSION_EMAIL_KEY, None)


def login_user(email):
    if email is None:
        return
    # make sure we clear any current login info
    logout_user(email)
    # now create a new session token
    login_token = get_random_token_for_login_session(email, n_bytes=32)
    # and store that puppy in the session cookie
    session[SESSION_TOKEN_KEY] = login_token
    session[SESSION_EMAIL_KEY] = email
    # as well as the sessions table
    km_user_sessions.create_session_token(g.db, email, login_token)
    # and mark that they just logged in
    km_users.update_last_login(g.db, email)
    km_events.create_event(g.db, email, 'login')


####################
# Security Helpers #
####################


def get_random_bytes(n_bytes=32):
    return os.urandom(n_bytes)


def get_random_token(n_bytes=32):
    return get_random_bytes(n_bytes).hex()


def get_random_token_for_pass_reset(email, n_bytes=32):
    tok = get_random_token(n_bytes)
    post = bytes(email, 'utf-8').hex()
    return tok + post


def get_random_token_for_login_session(email, n_bytes=32):
    tok = get_random_token(n_bytes)
    post = bytes(email, 'utf-8').hex()
    return tok + post


BCRYPT_ITER = secret.bcrypt_iter


def hash_password(password):
    password = password.encode('utf-8')
    return bcrypt.hashpw(password, bcrypt.gensalt(BCRYPT_ITER))


def password_matches_hash(unhashed_pass, hashed_pass):
    unhashed_pass = unhashed_pass.encode('utf-8')
    hashed_pass = hashed_pass.encode('utf-8')
    return bcrypt.checkpw(unhashed_pass, hashed_pass)

#################
# Email Helpers #
#################


def looks_like_email_address(email_addr):
    # TODO make this smarter
    # just check for an @ with some text left and right
    if email_addr is None or len(email_addr) < 3:
        return False
    parts = email_addr.split('@')
    return len(parts) == 2 and len(parts[0]) > 0 and len(parts[1]) > 0


def send_email(from_addr, to_addr, subject, body, api_token):
    postmark_client = PostmarkClient(server_token=api_token)
    postmark_client.emails.send(
        From=from_addr,
        To=to_addr,
        Subject=subject,
        HtmlBody=body)


def send_signup_email(to_addr, password_token):
    # gather our data
    from_addr = 'kinderminer@morgridge.org'
    subject = 'KinderMiner Signup'
    reset_link = ('https://www.kinderminer.org/choose_password/'
                  + password_token)
    # TODO this should probably be a rendered template instead
    body = '''Hi {0},<br>Thanks for signing up to use KinderMiner.<br>
        <br>Click (or copy and paste) the following link to set your new account
        password:<br>{1}'''.format(to_addr, reset_link)
    # send it
    send_email(from_addr, to_addr, subject, body, secret.email_api_token)


def send_forgot_pass_email(to_addr, password_token):
    # gather our data
    from_addr = 'kinderminer@morgridge.org'
    subject = 'KinderMiner Password Reset'
    reset_link = ('https://www.kinderminer.org/choose_password/'
                  + password_token)
    # TODO this should probably be a rendered template instead
    body = '''Hi {0},<br>A KinderMiner password reset has been requested for
        this account.<br><br>Click (or copy and paste) the following link to
        reset your account password:<br>{1}'''.format(to_addr, reset_link)
    # send it
    send_email(from_addr, to_addr, subject, body, secret.email_api_token)

##################
# Result Helpers #
##################


class ResultTuple:
    def __init__(
            self,
            target,
            target_count,
            keyphrase_count,
            target_and_keyphrase_count,
            db_count,
            target_and_keyphrase_ratio,
            p_value):
        self.target = target
        self.target_count = target_count
        self.keyphrase_count = keyphrase_count
        self.target_and_keyphrase_count = target_and_keyphrase_count
        self.db_count = db_count
        self.target_and_keyphrase_ratio = target_and_keyphrase_ratio
        self.p_value = p_value

    def csv_str(self):
        return ','.join([str(self.target), str(self.target_count),
                         str(self.target_and_keyphrase_count),
                         str(self.keyphrase_count),
                         str(self.db_count), str(self.p_value),
                         str(self.target_and_keyphrase_ratio)])


def get_result_list(result_dict):
    # do a quick check for some result content
    # TODO betterify this
    if 'db_article_cnt' not in result_dict:
        # no results to display really
        return list()
    # pull the static counts
    db_count = try_parse_int(result_dict['db_article_cnt'])
    kp_count = try_parse_int(result_dict['kp_cnt'])
    # and then the ordered lists for per target info
    # TODO thes should all be the same length
    targs = result_dict['target']
    targ_counts = result_dict['targ_cnt']
    targ_with_kp_counts = result_dict['targ_with_kp_cnt']
    targ_with_kp_ratios = result_dict['targ_and_kp_ratio']
    p_values = result_dict['fet_p_value']
    # now turn those into Result objects
    res = list()
    for i in range(len(targs)):
        # convert the values for this target
        t = targs[i]
        tc = try_parse_int(targ_counts[i])
        tkpc = try_parse_int(targ_with_kp_counts[i])
        tkpr = try_parse_float(targ_with_kp_ratios[i])
        p = try_parse_float(p_values[i])
        # and instantiate
        res.append(ResultTuple(t, tc, kp_count, tkpc, db_count, tkpr, p))
    # send them back
    return res


def get_result_csv_string(result_dict, p_val_filter=1.0):
    results = get_result_list(result_dict)
    # filter out those that don't meet the filter
    results = [r for r in results if r.p_value <= p_val_filter]
    # and sort them in descending order by the ratio
    results = sorted(
        results,
        key=lambda x: x.target_and_keyphrase_ratio,
        reverse=True)
    header = ','.join(['target','target_count','target_and_keyphrase_count',
                       'keyphrase_count','database_count','p_value',
                       'target_and_keyphrase_ratio'])
    csv_body = '\n'.join([r.csv_str() for r in results])
    return header +'\n' + csv_body + '\n'


########################
# Controller Endpoints #
########################


@app.before_request
def before_request():
    g.db = mysql.connect()


@app.teardown_request
def teardown_request(exception):
    if g.db is not None:
        g.db.close()


@app.route('/static/<filename>')
def server_static(filename):
    return send_from_directory('static', filename)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/')
def home():
    if not logged_in():
        return redirect('/login')
    return redirect('/request_form')


@app.route('/about')
def about():
    # the navbar need info about logged in user
    user = get_logged_in_user()
    return render_template('about.html', curr_user=user)


@app.route('/request_form', methods=['GET'])
def request_form():
    # login is required
    # TODO maybe make this into a decorator for all functions requiring login
    if not logged_in():
        return redirect('/login')
    # otherwise, go ahead and show it
    curr_year = datetime.datetime.now().year
    return render_template('request_form.html', curr_year=curr_year)


@app.route('/add_request', methods=['POST'])
def add_request():
    print('hit add_request')
    # login is required
    # TODO maybe make this into a decorator for all functions requiring login
    if not logged_in():
        return redirect('/login')
    # grab the query essentials
    query_name = request.form.get('query_name')
    key_phrase = request.form.get('key_phrase')
    target_terms = request.form.get('target_terms')
    sep_kp = request.form.get('sep_kp')
    censor_year = request.form.get('censor_year')
    user = get_logged_in_user()
    # break this out and provide useful feedback when not enough info
    success = True
    message = 'Job Submitted'
    # don't necessarily need to a query name
    # need at least something for the key phrase
    if key_phrase is None or len(key_phrase) < 1:
        success = False
        message = 'Please enter a Key Phrase'
    # need at least something for the target terms too
    if target_terms is None or len(target_terms) < 1:
        success = False
        message = 'Please enter Target Terms (one per line)'
    # the sep_kp option just can't be null
    sep_kp = to_bool(sep_kp)
    if sep_kp is None:
        success = False
        message = 'Problem with Sep KP checkbox'
    # and censor year just needs something for now
    censor_year = try_parse_int(censor_year)
    if censor_year is None:
        success = False
        message = 'Must select a Censor Year'
    # submit it if we have good data
    print({success, message})
    if success:
        # put the request parameters into a dict to be serialized
        params = dict()
        params['key_phrase'] = key_phrase.strip()
        params['target_terms'] = target_terms.strip()
        params['sep_kp'] = sep_kp
        params['censor_year'] = censor_year
        km_requests.submit_request(g.db, user.email, query_name, params)
        # mark the request event
        km_events.create_event(g.db, user.email, 'submit_request')
    return jsonify({'success': success, 'message': message})


@app.route('/results', methods=['GET'])
def results():
    # login is required
    # TODO maybe make this into a decorator for all functions requiring login
    if not logged_in():
        return redirect('/login')
    user = get_logged_in_user()
    user_requests = km_requests.select_by_email(g.db, user.email)
    # let's split up the pending and complete requests here
    pending_reqs = list()
    complete_reqs = list()
    for req in user_requests:
        if req.done:
            complete_reqs.append(req)
        else:
            pending_reqs.append(req)
    # sort by completion time
    sorted_pending_reqs = sorted(pending_reqs, key=lambda x: x.submit_time)
    sorted_complete_reqs = sorted(complete_reqs, key=lambda x: x.complete_time)
    return render_template('results.html',
                        pending_reqs=reversed(sorted_pending_reqs),
                        complete_reqs=reversed(sorted_complete_reqs))


@app.route('/results/<request_id>', methods=['GET'])
def results_table(request_id):
    print('hit results_table')
    # login is required
    # TODO maybe make this into a decorator for all functions requiring login
    if not logged_in():
        return redirect('/login')
    user = get_logged_in_user()
    # now we need to make sure that this request is owned by this user
    req = km_requests.try_select_by_id_if_email_match(
        g.db, request_id, user.email)
    if req is None:
        return redirect('/results')
    # turn the results into something we can render
    results = get_result_list(req.results)
    # and sort them in descending order by the ratio
    results = sorted(
        results,
        key=lambda x: x.target_and_keyphrase_ratio,
        reverse=True)
    # get the unique p-values for the slider
    # TODO maybe cut down even further to speed things up
    p_vals = sorted({r.p_value for r in results})
    no_hit_count = sum(res.target_and_keyphrase_count == 0 for res in results)
    request_name = req.name
    key_phrase = req.params['key_phrase']
    return render_template(
        'results_table.html',
        results=results,
        no_hit_count=no_hit_count,
        request_name=request_name,
        key_phrase=key_phrase,
        p_vals=p_vals,
        request_id=request_id)


@app.route('/download_results/<request_id>', methods=['GET'])
def download_results(request_id):
    print('hit download_results')
    # login is required
    # TODO maybe make this into a decorator for all functions requiring login
    if not logged_in():
        return redirect('/login')
    user = get_logged_in_user()
    # now we need to make sure that this request is owned by this user
    req = km_requests.try_select_by_id_if_email_match(
        g.db, request_id, user.email)
    if req is None:
        return redirect('/results')
    # try to get the FET cutoff for filtered results
    fet_cutoff = try_parse_float(request.args.get('fet_cutoff'))
    if fet_cutoff is None:
        fet_cutoff = 1.0
    # turn the results into a csv string to return
    ret_csv = get_result_csv_string(req.results, p_val_filter=fet_cutoff)
    return ret_csv


@app.route('/request_parameters/<request_id>', methods=['GET'])
def request_parameters(request_id):
    print('hit request_parameters')
    # login is required
    # TODO maybe make this into a decorator for all functions requiring login
    if not logged_in():
        return redirect('/login')
    user = get_logged_in_user()
    # now we need to make sure that this request is owned by this user
    req = km_requests.try_select_by_id_if_email_match(
        g.db, request_id, user.email)
    if req is None:
        return redirect('/results')
    return render_template('request_parameters.html', req=req)


@app.route('/delete_request', methods=['POST'])
def delete_request():
    print('hit delete_request')
    # login is required
    # TODO maybe make this into a decorator for all functions requiring login
    if not logged_in():
        return redirect('/login')
    user = get_logged_in_user()
    # check for the relevant request information
    request_id = request.form.get('request_id')
    if request_id is None:
        return redirect('/results')
    # now we need to make sure that this request is owned by this user
    req = km_requests.try_select_by_id_if_email_match(
        g.db, request_id, user.email)
    # is it a valid delete request?
    if req is not None:
        # go ahead and delete it then
        km_requests.delete_by_id(g.db, request_id)
    return redirect('/results')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    if request.method == 'POST':
        # just received a request to sign up with a particular email
        user_email = request.form.get('user_email')
        # first check if there is already account for that email
        if km_users.is_email_already_taken(g.db, user_email):
            return render_template(
                'signup.html',
                message='An account for that email already exists.')
        # and do a quick check to see if it even looks like they used an email
        if not looks_like_email_address(user_email):
            return render_template(
                'signup.html',
                message='Please register with an email address.')
        # otherwise create an account with a temp
        # password and send a reset email
        # first the account creation
        temp_pass = get_random_token()
        temp_passhash = hash_password(temp_pass)
        km_users.create_user_account(g.db, user_email, temp_passhash)
        # then the reset token
        # guarantee there are no other reset tokens for this email
        km_reset_tokens.delete_by_email(g.db, user_email)
        # generate a unique reset token based on 32-byte random + email
        reset_token = get_random_token_for_pass_reset(user_email, n_bytes=32)
        km_reset_tokens.insert_token(g.db, reset_token, user_email)
        # send them an email with the reset link
        send_signup_email(user_email, reset_token)
        return render_template(
            'signup.html',
            message='We have received your signup request. You will receive an email shortly.')


@app.route('/login_as_guest', methods=['POST'])
def login_as_guest():
    # generate a dummy guest email and password
    guest_email = 'guest' + get_random_token()
    guest_passhash = hash_password(get_random_token())
    # create a guest account from that info
    km_users.create_guest_user_account(g.db, guest_email, guest_passhash)
    # login that account
    login_user(guest_email)
    # redirect to the request form
    return redirect('/request_form')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if logged_in():
            return redirect('/request_form')
        return render_template('login.html')
    if request.method == 'POST':
        # first grab the login data
        email = request.form.get('email')
        password = request.form.get('password')
        # see if we even have a user by that email
        user = km_users.get_one_by_email(g.db, email)
        if user is None:
            return render_template(
                'login.html', message='Invalid email and/or password')
        # next check the entered password against the hash
        if user is None or not password_matches_hash(password, user.pass_hash):
            return render_template(
                'login.html', message='Invalid email and/or password')
        # otherwise, we can log them in and send them to the request form
        # first set up their session
        login_user(email)
        # and redirect them
        return redirect('/request_form')


@app.route('/logout', methods=['GET'])
def logout():
    # try to clear info if actually logged in
    user = get_logged_in_user()
    if user is not None:
        logout_user(user.email)
    # and always head over to the login page
    return redirect('/login')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot_password.html')
    if request.method == 'POST':
        # first grab the requested account for reset
        email = request.form.get('email')
        # get the associated user if they exist
        user = km_users.get_one_by_email(g.db, email)
        if user is not None:
            # guarantee there are no other reset tokens for this email
            km_reset_tokens.delete_by_email(g.db, email)
            # generate a unique reset token based on 32-byte random + email
            reset_token = get_random_token_for_pass_reset(email, n_bytes=32)
            km_reset_tokens.insert_token(g.db, reset_token, email)
            # send them an email with the reset link
            if not user.is_guest: # never send emails to guest accounts
                send_forgot_pass_email(email, reset_token)
        # give them some confirmation, even if the account doesn't exist
        message = 'Password reset request received. Check your email.'
        return render_template('forgot_password.html', message=message)


@app.route('/choose_password/<token>', methods=['GET'])
def choose_password(token):
    res_cred = km_reset_tokens.get_one_by_token(g.db, token)
    if res_cred is not None:
        return render_template(
            'choose_password.html',
            reset_token=res_cred.token)
    else:
        return redirect('/login')


@app.route('/set_password', methods=['POST'])
def set_password():
    print('hit set_password')
    # we just received a reset request
    reset_token = request.form.get('reset_token')
    new_pass = request.form.get('new_pass')
    success = True
    success_message = 'Your password has been changed'
    missing_credentials_message = 'Missing token or password'
    invalid_credentials_message = ('Either your reset credentials are expired'
        ' or invalid, please go through the password reset process to change'
        ' it again.')
    # did we get all the necessary information?
    if reset_token is None or new_pass is None:
        # TODO better error messaging
        success = False
        return jsonify({'success': success,
                        'message': missing_credentials_message})
    # we have what we need
    res_cred = km_reset_tokens.get_one_by_token(g.db, reset_token)
    if res_cred is not None:
        # set the new password
        pw_hash = hash_password(new_pass)
        km_users.reset_pass_hash(g.db, res_cred.email, pw_hash)
        # and clear the reset token for this account
        km_reset_tokens.delete_by_email(g.db, res_cred.email)
        # done
        return jsonify({'success': success, 'message': success_message})
    else:
        success = False
        return jsonify({'success': success,
                        'message': invalid_credentials_message})


if __name__ == '__main__':
    app.secret_key = get_random_bytes(32)
    app.run(debug=secret.web_debug, host=secret.web_host, port=secret.web_port)
