import flask
import flask_bootstrap
import flask_login
import flask_moment
import json
import os

import google_auth_oauthlib
import oauthlib.oauth2
import requests

import google_auth_oauthlib.flow

import app.db as db
import app.dict_manager as dict_manager
import app.forms as forms
import app.portal_requests as portal_requests

from app.user import User
from config import CONFIG, SCOPES

CLIENT_SECRETS_FILE = 'client_secret.json'
with open(CLIENT_SECRETS_FILE) as data_file:
    SECRETS = json.load(data_file)

GOOGLE_CLIENT_ID = str(SECRETS['web']['client_id'])
GOOGLE_CLIENT_SECRET = str(SECRETS['web']['client_secret'])
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

API_SERVICE_NAME = 'cloud-platform'
API_VERSION = 'v1'

bootstrap = flask_bootstrap.Bootstrap()
login_manager = flask_login.LoginManager()
moment_manager = flask_moment.Moment()

CSRF_ENABLED = True
app = flask.Flask(__name__)
app.secret_key = GOOGLE_CLIENT_SECRET
bootstrap.init_app(app)
login_manager.init_app(app)
moment_manager.init_app(app)
db.init_app(app)

CLIENT = oauthlib.oauth2.WebApplicationClient(GOOGLE_CLIENT_ID)


def get_google_provider_config():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@app.before_request
def check_under_maintenance():
    if CONFIG['OPTIONS']['MAINTENANCE'] == 1:
        flask.abort(503)


@app.route('/', methods=['GET', 'POST'])
def index():
    authenticated = flask_login.current_user.is_authenticated
    if authenticated:
        display = flask_login.current_user.display
        registered = flask_login.current_user.registered
        billable = flask_login.current_user.billable

        status = {'authenticated': authenticated, 'registered': registered, 'billable': billable}
        if registered == 200 and billable == 200:
            return flask.redirect(flask.url_for('user'))
        else:
            registration, billing = check_status(flask_login.current_user.access_token)
            User.update_status(flask_login.current_user.id, registration, billing)
            return flask.render_template('index.html', display=display, status=status, CONFIG=CONFIG)
    else:
        status = {'authenticated': False, 'registered': 400, 'billable': 400}
        return flask.render_template('index.html', display='', status=status, CONFIG=CONFIG)


@app.route('/user', methods=['GET', 'POST'])
@flask_login.login_required
def user():
    display = flask_login.current_user.display
    return flask.render_template('user.html', display=display, CONFIG=CONFIG)


@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload():
    if not portal_requests.FireCloud.get_health().ok:
        return flask.redirect(flask.url_for('terra_down'))

    display = flask_login.current_user.display
    oncotree = dict_manager.Oncotree.create_oncotree()

    credentials = dict_manager.Credentials.for_google(flask_login.current_user, SECRETS)
    if dict_manager.DateTime.time_to_renew_token(flask_login.current_user.time_authorized):
        response = refresh_token(credentials)
        token = response
    else:
        token = flask_login.current_user.access_token

    form = forms.UploadForm()
    form.billingProject.choices = portal_requests.Launch.list_billing_projects(token)
    if flask.request.method == 'POST' and form.validate_on_submit():
        profile = dict_manager.Form.populate_patient(form)
        portal_requests.Launch.submit_patient(token, profile, credentials)
        return flask.redirect(flask.url_for('user'))
    return flask.render_template('upload.html',
                                 display=display,
                                 CONFIG=CONFIG,
                                 form=form,
                                 billing_projects=form.billingProject.choices,
                                 oncotree_list=oncotree)


@app.route('/submissions', methods=['GET', 'POST'])
@flask_login.login_required
def submissions():
    if not portal_requests.FireCloud.get_health().ok:
        return flask.redirect(flask.url_for('terra_down'))

    display = flask_login.current_user.display
    credentials = dict_manager.Credentials.for_google(flask_login.current_user, SECRETS)
    if dict_manager.DateTime.time_to_renew_token(flask_login.current_user.time_authorized):
        response = refresh_token(credentials)
        token = response
    else:
        token = flask_login.current_user.access_token

    patient_table = portal_requests.Launch.list_workspaces(token)
    return flask.render_template('submissions.html', display=display, CONFIG=CONFIG, patient_table=patient_table)


@app.route('/terra_down')
@flask_login.login_required
def terra_down():
    return flask.render_template('terra_down.html', display=flask_login.current_user.display, CONFIG=CONFIG)


@app.route('/report/<namespace>/<name>/<bucket>', methods=['GET', 'POST'])
@flask_login.login_required
def display_report(namespace=None, name=None, bucket=None):
    credentials = dict_manager.Credentials.for_google(flask_login.current_user, SECRETS)
    if dict_manager.DateTime.time_to_renew_token(flask_login.current_user.time_authorized):
        response = refresh_token(credentials)
        token = response
    else:
        token = flask_login.current_user.access_token
    credentials['token'] = token
    credentials_for_google = portal_requests.GCloud.authorize_credentials(credentials)

    namespace = namespace
    name = name
    bucket = bucket

    workspace_datamodel = portal_requests.Launch.get_datamodel(token, namespace, name)
    url = workspace_datamodel.loc[0, 'report']
    obj = url.replace(f'gs://{bucket}/', '')

    initialized_bucket = portal_requests.GCloud.initialize_bucket(credentials_for_google, bucket)
    blob = portal_requests.GCloud.download_as_string(initialized_bucket, obj)
    return blob.decode('utf-8')


@app.errorhandler(503)
def maintenance(e):
    authenticated = flask_login.current_user.is_authenticated
    if authenticated:
        display = flask_login.current_user.display
    else:
        display = ''
    return flask.render_template('503.html', display=display, CONFIG=CONFIG), 503


@app.errorhandler(404)
def page_not_found(e):
    authenticated = flask_login.current_user.is_authenticated
    if authenticated:
        display = flask_login.current_user.display
    else:
        display = ''
    return flask.render_template('404.html', display=display, CONFIG=CONFIG), 404


@app.route('/terms')
def terms():
    authenticated = flask_login.current_user.is_authenticated
    if authenticated:
        display = flask_login.current_user.display
    else:
        display = ''
    return flask.render_template('terms.html', display=display, CONFIG=CONFIG)


@app.route('/privacy')
def privacy():
    authenticated = flask_login.current_user.is_authenticated
    if authenticated:
        display = flask_login.current_user.display
    else:
        display = ''
    return flask.render_template('privacy.html', display=display, CONFIG=CONFIG)


@app.route('/login')
def login():
    return flask.redirect(flask.url_for('authorize'))


@app.route('/login/authorize')
def authorize():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(access_type='offline',
                                                      include_granted_scopes='true',
                                                      prompt='consent')
    flask.session['state'] = state
    return flask.redirect(authorization_url)


@app.route('/login/callback')
def oauth2callback():
    state = flask.session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE,
                                                                   state=state,
                                                                   scopes=SCOPES)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = dict_manager.Credentials.json_to_dictionary(flow.credentials.to_json())
    token = credentials['token']
    refresh = credentials['refresh_token']
    scopes = credentials['scopes']

    user_information = portal_requests.Launch.get_profile(token)
    unique_id = user_information['id']
    email = user_information['email']

    returning_user = User.get(unique_id)
    if not returning_user:
        registration, billing = check_status(token)
        User.create(unique_id, email, registration, billing, token, refresh, scopes)
    else:
        if not returning_user.registered == 200 or not returning_user.billable == 200:
            registration, billing = check_status(token)
            User.update_status(unique_id, registration, billing)
        User.update_tokens(unique_id, token, refresh, scopes)
    current_user = User.get(unique_id)

    flask_login.login_user(current_user)
    flask.flash('Logged in successfully')
    return flask.redirect(flask.url_for('index'))


@app.route("/logout")
@flask_login.login_required
def logout():
    clear_session()
    flask_login.logout_user()
    flask.flash("Logged out successfully")
    return flask.redirect(flask.url_for("index"))


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


def clear_session():
    flask.session.clear()
    [flask.session.pop(key) for key in list(flask.session.keys())]


def refresh_token(credentials):
    return portal_requests.Launch.refresh_token(credentials)


def check_status(token):
    registration = portal_requests.Terra.check_registration(token)
    billing = portal_requests.Terra.get_billing_projects(token)
    registration_code = registration.status_code
    billing_code = 200 if len(billing.json()) > 0 else 401
    return registration_code, billing_code
