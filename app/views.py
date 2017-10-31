import json
from flask import Flask, redirect, render_template, request, session, url_for
from flask_bootstrap import Bootstrap
from flask_oauthlib.client import OAuth
from gevent import wsgi

from csportalRequests import firecloud_functions, firecloud_requests, gcloud_requests, launch_requests
from dictManager import statusDict, userDict, oncoTree
from forms import UploadForm

with open('app/config_secrets.json') as data_file:
    config = json.load(data_file)

GOOGLE_CLIENT_ID = str(config['secret']['GOOGLE_CLIENT_ID'])
GOOGLE_CLIENT_SECRET = str(config['secret']['GOOGLE_CLIENT_SECRET'])
REDIRECT_URL = '/oauth2callback'

CSRF_ENABLED = True
app = Flask(__name__)
app.debug = True
app.secret_key = str(config['secret']['APP_SECRET_KEY'])

bootstrap = Bootstrap(app)
oauth = OAuth(app)

google = oauth.remote_app('google',
                          consumer_key=GOOGLE_CLIENT_ID,
                          consumer_secret=GOOGLE_CLIENT_SECRET,
                          request_token_params={
                              'scope': ['email', 'https://www.googleapis.com/auth/cloud-platform'],
                          },
                          request_token_url=None,
                          base_url='https://www.googleapis.com/oauth2/v1/',
                          access_token_method='POST',
                          access_token_url='https://accounts.google.com/o/oauth2/token',
                          authorize_url='https://accounts.google.com/o/oauth2/auth'
                          )

# https://cloud.google.com/compute/docs/access/service-accounts
# https://google-auth.readthedocs.io/en/latest/user-guide.html#service-account-private-key-files

@app.route('/', methods = ['GET', 'POST'])
def index():
    status_dict = statusDict.new_dict()
    user_dict = userDict.new_dict()

    session['firecloudHealth'] = firecloud_requests.get_health()
    if not session.get('firecloudHealth'):
        return redirect(url_for('firecloud_down'))

    if 'google_token' in session:
        access_token = session.get('google_token')[0]
        status_dict = firecloud_functions.populate_status(status_dict, access_token)
        user_dict = userDict.populate_googleauth(user_dict, google)

    if firecloud_functions.evaluate_upload_status(status_dict):
        # Pass status_dict and user_dict https://stackoverflow.com/questions/17057191/flask-redirect-while-passing-arguments
        return redirect(url_for('user'))
    else:
        return render_template('index.html', status_dict=status_dict, user_dict=user_dict)

@app.route('/user', methods = ['GET', 'POST'])
def user():
    status_dict = statusDict.new_dict()
    user_dict = userDict.new_dict()

    if 'google_token' not in session:
        return redirect(url_for('index'))

    if not session.get('firecloudHealth'):
        return redirect(url_for('firecloud_down'))

    access_token = session.get('google_token')[0]
    status_dict = firecloud_functions.populate_status(status_dict, access_token)
    user_dict = userDict.populate_googleauth(user_dict, google)
    patient_table = launch_requests.launch_list_workspaces(access_token)

    return render_template('user.html', status_dict=status_dict, user_dict=user_dict,
                           patient_table=patient_table)

@app.route('/upload', methods = ['GET', 'POST'])
def upload():
    status_dict = statusDict.new_dict()
    user_dict = userDict.new_dict()

    if 'google_token' not in session:
        return redirect(url_for('index'))

    if not session.get('firecloudHealth'):
        return redirect(url_for('firecloud_down'))

    access_token = session.get('google_token')[0]
    credentials = session.get('credentials')
    status_dict = firecloud_functions.populate_status(status_dict, access_token)
    user_dict = userDict.populate_googleauth(user_dict, google)
    user_dict = firecloud_functions.populate_user(user_dict, access_token)
    oncotree_list = oncoTree.create_oncoTree_unicode()

    form = UploadForm()
    form.billingProject.choices = user_dict['firecloud_billing']
    if request.method == 'POST' and form.validate_on_submit():
        patient = {}
        patient['billingProject'] = form.billingProject.data
        patient['patientId'] = request.form['patientId']
        patient['tumorType'] = request.form['tumorType']
        patient['description'] = form.description.data
        patient['snvHandle'] = request.files['snvHandle']
        patient['indelHandle'] = request.files['indelHandle']
        patient['burdenHandle'] = request.files['burdenHandle']
        patient['segHandle'] = request.files['segHandle']
        patient['fusionHandle'] = request.files['fusionHandle']
        patient['dnarnaHandle'] = request.files['dnarnaHandle']
        patient['germlineHandle'] = request.files['germlineHandle']

        patient['tumorTypeShort'] = oncoTree.extract_shortcode(patient['tumorType'])
        patient['tumorTypeLong'] = oncoTree.extract_longcode(patient['tumorType'])

        launch_requests.launch_csPortal(access_token, patient)

        return redirect(url_for('user'))

    return render_template('upload.html', status_dict=status_dict, user_dict=user_dict,
                           form=form, oncotree=oncotree_list)

@app.route('/firecloud_down')
def firecloud_down():
    status_dict = statusDict.new_dict()
    user_dict = userDict.new_dict()

    if 'google_token' in session:
        access_token = session.get('google_token')[0]
        status_dict = firecloud_functions.populate_status(status_dict, access_token)
        user_dict = userDict.populate_googleauth(user_dict, google)

    return render_template('firecloud_down.html', status_dict=status_dict, user_dict=user_dict)

@app.errorhandler(404)
def page_not_found(e):
    status_dict = statusDict.new_dict()
    user_dict = userDict.new_dict()

    if not session.get('firecloudHealth'):
        return redirect(url_for('firecloud_down'))

    if 'google_token' in session:
        access_token = session.get('google_token')[0]
        status_dict = firecloud_functions.populate_status(status_dict, access_token)
        user_dict = userDict.populate_googleauth(user_dict, google)

    return render_template('404.html', status_dict=status_dict, user_dict=user_dict), 404

@app.route('/login')
def login():
    callback=url_for('authorized', _external=True)
    return google.authorize(callback=callback)

@app.route('/logout')
def logout():
    if 'google_token' in session:
        access_token = session.get('google_token')[0]
        gcloud_requests.revoke_token(access_token)
    session.clear()
    return redirect(url_for('index'))

@app.route(REDIRECT_URL)
def authorized():
    resp = google.authorized_response()
    if resp is None:
        return 'Access_denied: reasons=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )

    print resp
    session['google_token'] = (resp['access_token'], '')
    session['credentials'] = resp
    return redirect(url_for('index'))

@google.tokengetter
def get_access_token():
    return session.get('google_token')

if __name__ == "__main__":
    app.run(threaded=True)
#    server = wsgi.WSGIServer(('localhost', 5000), app)
#    server.serve_forever()