import json
import flask
import flask_bootstrap
import flask_moment
import dataset

import google_auth_oauthlib.flow
import google.auth.transport.requests

import app.portal_requests as portal_requests
import app.dict_manager as dict_manager
import app.forms as forms
import app.log as log

from time import time

CLIENT_SECRETS_FILE = 'client_secret.json'
with open(CLIENT_SECRETS_FILE) as data_file:
    config = json.load(data_file)

SCOPES = ['email', 'https://www.googleapis.com/auth/cloud-platform']
API_SERVICE_NAME = 'cloud-platform'
API_VERSION = 'v1'

DB = 'sqlite:///submissions.db'
ADMIN = 'admin'
db = dataset.connect(DB)

CSRF_ENABLED = True
app = flask.Flask(__name__)
app.secret_key = str(config['web']['client_secret'])

moment = flask_moment.Moment(app)
bootstrap = flask_bootstrap.Bootstrap(app)


@app.before_request
def check_under_maintenance():
    var_maintenance = 1
    if var_maintenance == 1:
        flask.abort(503)


@app.route('/', methods=['GET', 'POST'])
def index():
    credentials = initialize_page()
    user_ready = dict_manager.StatusDict.evaluate(flask.session['status_dict'])
    if user_ready:
        return flask.redirect(flask.url_for('user'))
    else:
        return flask.render_template('index.html',
                                     status_dict=flask.session['status_dict'],
                                     user_dict=flask.session['user_dict'])


@app.route('/user', methods=['GET', 'POST'])
def user():
    credentials = initialize_page()
    user_ready = dict_manager.StatusDict.evaluate(flask.session['status_dict'])
    if not user_ready:
        return flask.redirect(flask.url_for('index'))
    else:
        patient_table = portal_requests.Launch.list_workspaces(credentials.token)
        return flask.render_template('user.html',
                                     status_dict=flask.session['status_dict'],
                                     user_dict=flask.session['user_dict'],
                                     patient_table=patient_table)


@app.route('/upload', methods = ['GET', 'POST'])
def upload():
    credentials = initialize_page()
    user_ready = dict_manager.StatusDict.evaluate(flask.session['status_dict'])
    if not user_ready:
        return flask.redirect(flask.url_for('index'))
    else:
        oncotree_list = dict_manager.Oncotree.create_oncotree()
        form = forms.UploadForm()
        form.billingProject.choices = portal_requests.Launch.list_billing_projects(credentials.token)
        if flask.request.method == 'POST' and form.validate_on_submit():
            patient = dict_manager.Form.populate_patient(form)
            portal_requests.Launch.submit_patient(credentials, patient)
            log.AppendDb.record(flask.session['user_dict']['email'])

            return flask.redirect(flask.url_for('user'))

        return flask.render_template('upload.html',
                                     status_dict=flask.session['status_dict'],
                                     user_dict=flask.session['user_dict'],
                                     billing_projects=form.billingProject.choices,
                                     form=form,
                                     oncotree=oncotree_list)


@app.route('/history')
def history():
    credentials = initialize_page()
    if db[ADMIN].find_one(email=flask.session['user_dict']['email']):
        return flask.render_template('history.html',
                                     status_dict=flask.session['status_dict'],
                                     user_dict=flask.session['user_dict'],
                                     db=db['submissions'])
    else:
        return flask.render_template('404.html',
                                     status_dict=flask.session['status_dict'],
                                     user_dict=flask.session['user_dict']), 404


@app.route('/firecloud_down')
def firecloud_down():
    flask.session['firecloudHealth'] = portal_requests.FireCloud.get_health().ok
    if flask.session['firecloudHealth']:
        return flask.redirect(url_for('index'))
    else:
        return flask.render_template('firecloud_down.html',
                                     status_dict=flask.session['status_dict'],
                                     user_dict=flask.session['user_dict'])


@app.errorhandler(503)
def maintenance(e):
    credentials = initialize_page()
    return flask.render_template('503.html',
                                 status_dict=flask.session['status_dict'],
                                 user_dict=flask.session['user_dict'])


@app.errorhandler(404)
def page_not_found(e):
    credentials = initialize_page()
    return flask.render_template('404.html',
                                 status_dict=flask.session['status_dict'],
                                 user_dict=flask.session['user_dict']), 404


@app.route('/login')
def login():
    return flask.redirect(flask.url_for('authorize'))


@app.route('/authorize')
def authorize():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(
        access_type='offline', include_granted_scopes='true')

    flask.session['state'] = state
    return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    state = flask.session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)
    # Add comment for access denied

    flask.session['credentials'] = dict_manager.Credentials.credentials_to_dict(flow.credentials)
    flask.session['time_authorized'] = dict_manager.DateTime.datetime_for_session()
    flask.session['time_authorized_orginal'] = flask.session['time_authorized']
    return flask.redirect(flask.url_for('index'))


@app.route('/logout')
def logout():
    credentials = portal_requests.GCloud.authorize_credentials(flask.session['credentials'])
    r = portal_requests.GCloud.revoke_token(credentials.token) # Better handling for error codes
    flask.session.clear()
    return flask.redirect(flask.url_for('index'))


def refresh_token():
    refreshed_token = portal_requests.Launch.refresh_token(flask.session['credentials'])
    if refreshed_token == 'failed':
        flask.session.clear()
    else:
        flask.session['credentials']['token'] = refreshed_token
        flask.session['time_authorized'] = dict_manager.DateTime.datetime_for_session()


def update_status_dict(token):
    flask.session['status_dict'] = portal_requests.Launch.update_status_dict(
        flask.session['status_dict'], token)


def update_user_dict(token):
    flask.session['user_dict'] = portal_requests.Launch.update_user_dict(
        flask.session['user_dict'], token)


def initialize_page():
    flask.session['firecloudHealth'] = portal_requests.FireCloud.get_health().ok
    if not flask.session['firecloudHealth']:
        return flask.redirect(flask.url_for('firecloud_down'))

    if 'time_authorized' in flask.session:
        if dict_manager.DateTime.time_to_renew(flask.session['time_authorized']):
            refresh_token()

    if 'status_dict' not in flask.session:
        flask.session.clear()
        flask.session['status_dict'] = dict_manager.StatusDict.new_dict()
        flask.session['user_dict'] = dict_manager.UserDict.new_dict()

    if 'credentials' in flask.session:
        credentials = portal_requests.GCloud.authorize_credentials(flask.session['credentials'])
        flask.session['credentials'] = dict_manager.Credentials.credentials_to_dict(credentials)
        if "danger" in flask.session['status_dict'].values():
            update_status_dict(credentials.token)
        if '' in flask.session['user_dict'].values():
            update_user_dict(credentials.token)
        return credentials
    else:
        return ''
