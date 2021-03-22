import json
import requests
import google.oauth2.credentials
import app.dict_manager as dict_manager
from google.cloud import storage

from config import CONFIG


class GCloud:
    @staticmethod
    def authorize_credentials(flask_credentials):
        return google.oauth2.credentials.Credentials(**flask_credentials)

    @staticmethod
    def generate_headers(token):
        return {"Authorization": f"OAuth {token}"}

    @classmethod
    def get_profile(cls, header):
        request = "https://www.googleapis.com/oauth2/v2/userinfo"
        return requests.get(request, headers=header)

    @staticmethod
    def revoke_token(token):
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        request = "https://accounts.google.com/o/oauth2/revoke"
        return requests.get(request, headers=headers, params={'token': token})

    @staticmethod
    def refresh_token(credentials):
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        request = 'https://www.googleapis.com/oauth2/v4/token'
        params = {
            'client_id': credentials['client_id'],
            'client_secret': credentials['client_secret'],
            'refresh_token': credentials['refresh_token'],
            'grant_type': 'refresh_token'}
        return requests.post(request, headers=headers, params=params)

    @staticmethod
    def initialize_bucket(credentials, bucket_handle):
        gcs = storage.Client(credentials=credentials)
        return gcs.get_bucket(bucket_handle)

    @staticmethod
    def upload_to_bucket(bucket, file):
        blob = bucket.blob(file.filename)
        blob.upload_from_string(
            file.read(),
            content_type=file.content_type)

    @staticmethod
    def download_as_string(bucket, obj):
        blob = bucket.blob(obj)
        return blob.download_as_string()


class Terra:
    API_ROOT = "https://api.firecloud.org"

    @staticmethod
    def generate_headers(token):
        return {"Authorization": f"Bearer {token}", "X-App-ID": CONFIG['STRINGS']['APP_TAG']}

    @classmethod
    def check_registration(cls, token):
        headers = cls.generate_headers(token)
        request = f"{cls.API_ROOT}/me"
        return requests.get(request, headers=headers)

    @classmethod
    def copy_method(cls, token, workspace):
        headers = cls.generate_headers(token)
        headers["content-type"] = "application/json"

        namespace = workspace['namespace']
        name = workspace['name']

        method_namespace = CONFIG['METHOD']['NAMESPACE']
        method_name = CONFIG['METHOD']['NAME']
        method_snapshot = CONFIG['METHOD']['SNAPSHOT']

        payload = {
            "configurationNamespace": method_namespace,
            "configurationName": method_name,
            "configurationSnapshotId": int(method_snapshot),
            "destinationNamespace": method_namespace,
            "destinationName": method_name
        }

        request = f"{cls.API_ROOT}/api/workspaces/{namespace}/{name}/method_configs/copyFromMethodRepo"
        return requests.post(request, headers=headers, data=json.dumps(payload))

    @classmethod
    def get_billing_projects(cls, token):
        headers = cls.generate_headers(token)
        headers['accept'] = 'application/json'
        request = f"{cls.API_ROOT}/api/profile/billing"
        return requests.get(request, headers=headers)

    @classmethod
    def get_datamodel(cls, token, namespace, name, entity='pair'):
        headers = cls.generate_headers(token)
        request = f"{cls.API_ROOT}/api/workspaces/{namespace}/{name}/entities/{entity}/tsv"
        return requests.get(request, headers=headers)

    @classmethod
    def get_monitor_submission(cls, token, namespace, name, submission_id):
        headers = cls.generate_headers(token)
        headers['accept'] = 'application/json'
        request = f"{cls.API_ROOT}/api/workspaces/{namespace}/{name}/submissions/{submission_id}"
        return requests.get(request, headers=headers)

    @classmethod
    def get_workspaces(cls, token):
        headers = cls.generate_headers(token)
        request = f"{cls.API_ROOT}/api/workspaces"
        return requests.get(request, headers=headers)


class FireCloud(object):
    # https://api.firecloud.org/
    @staticmethod
    def generate_headers(token):
        return {"Authorization": f"Bearer {token}", }

    @staticmethod
    def get_health():
        request = "https://api.firecloud.org/health"
        return requests.get(request)

    @staticmethod
    def check_registration(headers):
        request = "https://api.firecloud.org/me"
        return requests.get(request, headers=headers)

    @staticmethod
    def get_billing_projects(headers):
        request = "https://api.firecloud.org/api/profile/billing"
        return requests.get(request, headers=headers)

    @staticmethod
    def get_monitor_submission(headers, namespace, name, submission_id):
        request = "https://api.firecloud.org/api/workspaces/"
        request += namespace + '/' + name + '/submissions/' + submission_id
        return requests.get(request, headers=headers)

    @staticmethod
    def create_new_workspace(headers, json):
        request = "https://api.firecloud.org/api/workspaces"
        return requests.post(request, headers=headers, json=json)

    @staticmethod
    def post_entities(headers, workspace_dict, entities_tsv):
        request = "https://api.firecloud.org/api/workspaces/"
        request += workspace_dict['namespace'] + "/" + workspace_dict['name'] + "/importEntities"
        return requests.post(request, headers=headers, data={"entities": entities_tsv})

    @staticmethod
    def post_attributes(headers, workspace_dict, attributes_tsv):
        headers["content-type"] = "application/x-www-form-urlencoded"
        request = "https://api.firecloud.org/api/workspaces/"
        request += workspace_dict['namespace'] + '/' + workspace_dict['name'] + '/importAttributesTSV'
        return requests.post(request, headers=headers, data={'attributes': attributes_tsv})

    @staticmethod
    def copy_method(headers, workspace_dict):
        namespace = "{}".format(CONFIG['METHOD']['NAMESPACE'])
        name = "{}".format(CONFIG['METHOD']['NAME'])
        snapshot = "{}".format(CONFIG['METHOD']['SNAPSHOT'])

        headers["content-type"] = "application/json"
        payload = {
            "configurationNamespace": namespace,
            "configurationName": name,
            "configurationSnapshotId": int(snapshot),
            "destinationNamespace": namespace,
            "destinationName": name}

        request = "https://api.firecloud.org/api/workspaces/"
        request += workspace_dict['namespace'] + '/' + workspace_dict['name'] + '/method_configs/copyFromMethodRepo'
        return requests.post(request, headers=headers, data=json.dumps(payload))

    @staticmethod
    def post_method_submission(headers, patient, workspace_dict):
        namespace = "{}".format(CONFIG['METHOD']['NAMESPACE'])
        name = "{}".format(CONFIG['METHOD']['NAME'])

        headers["content-type"] = "application/json"
        payload = {
            "methodConfigurationNamespace": namespace,
            "methodConfigurationName": name,
            "entityType": "pair",
            "entityName": patient['patientId'] + '-pair',
            "useCallCache": False,
            "workflowFailureMode": "NoNewCalls"
        }

        request = "https://api.firecloud.org/api/workspaces/"
        request += workspace_dict['namespace'] + '/' + workspace_dict['name'] + '/' + 'submissions'
        return requests.post(request, headers=headers, data=json.dumps(payload))


class Launch(object):
    @staticmethod
    def append_workflow_id(token, workspace):
        r = Terra.get_monitor_submission(token, workspace['namespace'], workspace['name'], workspace['submissionId'])
        return dict_manager.Submission.extract_workflow_id(r.json())

    @staticmethod
    def copy_method(token, workspace_dict):
        r = Terra.copy_method(token, workspace_dict)

    @staticmethod
    def create_new_workspace(token, patient):
        headers = FireCloud.generate_headers(token)
        workspace_json = dict_manager.NewWorkspace.populate_json(patient)
        new_workspace_request = FireCloud.create_new_workspace(headers, workspace_json)
        new_workspace_dict = new_workspace_request.json()
        new_workspace_dict['bucketHandle'] = dict_manager.NewWorkspace.create_gsBucket_address(
            new_workspace_dict['bucketName'])
        return new_workspace_dict

    @classmethod
    def get_datamodel(cls, token, namespace, name):
        r = Terra.get_datamodel(token, namespace, name)
        return dict_manager.DataModel.convert_content_to_dataframe(r.content)

    @classmethod
    def get_profile(cls, token):
        headers = GCloud.generate_headers(token)
        r = GCloud.get_profile(headers)
        if r.status_code == 200:
            return r.json()
        else:
            return f'Failed to retrieve user info from Google {r.status_code}\n{r.content}'

    @classmethod
    def list_billing_projects(cls, token):
        projects = Terra.get_billing_projects(token)
        return dict_manager.BillingProjects.extract_as_tuples(projects.json())

    @classmethod
    def list_workspaces(cls, token):
        workspaces = Terra.get_workspaces(token)
        table = dict_manager.PatientTable.generate(workspaces.json())
        for idx in table.index:
            table.loc[idx, 'workflowId'] = cls.append_workflow_id(token, table.loc[idx, :])
            table.loc[idx, 'reportUrl'] = dict_manager.PatientTable.create_report_blob(
                table.loc[idx, 'submissionId'], table.loc[idx, 'workflowId'], table.loc[idx, 'patientId'])
        return table

    @staticmethod
    def submit_bucket_upload(bucket, patient):
        handles = ['snvHandle', 'indelHandle', 'segHandle', 'fusionHandle',
                   'burdenHandle', 'germlineHandle', 'dnarnaHandle']
        for handle in handles:
            if patient[handle] != '':
                GCloud.upload_to_bucket(bucket, patient[handle])

    @staticmethod
    def submit_method(token, patient, workspace_dict):
        headers = FireCloud.generate_headers(token)
        submission = FireCloud.post_method_submission(headers, patient, workspace_dict)
        submission_id = dict_manager.Submission.extract_submission_id(submission.json())
        attributes_tsv = dict_manager.Submission.create_attributes_tsv(submission_id)
        FireCloud.post_attributes(headers, workspace_dict, attributes_tsv)

    @classmethod
    def submit_patient(cls, token, patient, credentials):
        credentials_for_google = GCloud.authorize_credentials(credentials)
        workspace_dict = cls.create_new_workspace(token, patient)
        bucket_id = dict_manager.NewWorkspace.extract_bucket_handle(workspace_dict)
        bucket = GCloud.initialize_bucket(credentials_for_google, bucket_id)
        # Add more error handling
        cls.submit_bucket_upload(bucket, patient)
        cls.update_datamodel(token, patient, workspace_dict)
        cls.copy_method(token, workspace_dict)
        cls.submit_method(token, patient, workspace_dict)

    @staticmethod
    def refresh_token(credentials):
        r = GCloud.refresh_token(credentials)
        if r.status_code == 200:
            return r.json()['access_token']
        else:
            return 'failed'

    @staticmethod
    def update_datamodel(token, patient, workspace_dict):
        participant_tsv = dict_manager.DataModel.create_participant_tsv(patient)
        sample_tsv = dict_manager.DataModel.create_sample_tsv(patient)
        pair_tsv = dict_manager.DataModel.create_pair_tsv(patient, workspace_dict)

        headers = FireCloud.generate_headers(token)
        r = FireCloud.post_entities(headers, workspace_dict, participant_tsv)
        r = FireCloud.post_entities(headers, workspace_dict, sample_tsv)
        r = FireCloud.post_entities(headers, workspace_dict, pair_tsv)
