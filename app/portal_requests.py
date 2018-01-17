import json
import requests
import google.oauth2.credentials
import app.dict_manager as dict_manager
from google.cloud import storage


class GCloud(object):
    @staticmethod
    def generate_headers(token):
        return {"Authorization": "OAuth %s" % str(token)}

    @classmethod
    def get_email(cls, header):
        request = "https://www.googleapis.com/oauth2/v2/userinfo"
        return requests.get(request, headers=header)

    @staticmethod
    def authorize_credentials(flask_credentials):
        return google.oauth2.credentials.Credentials(
            **flask_credentials)

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
    def initialize_bucket(credentials, workspace_dict):
        gcs = storage.Client(credentials=credentials)
        return gcs.get_bucket(workspace_dict['bucketHandle'].split('/')[2])

    @staticmethod
    def upload_to_bucket(bucket, file):
        blob = bucket.blob(file.filename)
        blob.upload_from_string(
            file.read(),
            content_type=file.content_type
        )


class FireCloud(object):
    # https://api.firecloud.org/
    @staticmethod
    def generate_headers(token):
        return {"Authorization": "bearer " + str(token)}

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
        headers["content-type"] = "application/json"
        payload = {
            "configurationNamespace": "breardon",
            "configurationName": "chips",
            "configurationSnapshotId": 47,
            "destinationNamespace": "breardon",
            "destinationName": "chips"}

        request = "https://api.firecloud.org/api/workspaces/"
        request += workspace_dict['namespace'] + '/' + workspace_dict['name'] + '/method_configs/copyFromMethodRepo'
        return requests.post(request, headers=headers, data=json.dumps(payload))

    @staticmethod
    def post_method_submission(headers, patient, workspace_dict):
        headers["content-type"] = "application/json"
        payload = {
            "methodConfigurationNamespace": "breardon",
            "methodConfigurationName": "chips",
            "entityType": "pair",
            "entityName": patient['patientId'] + '-pair',
            "useCallCache": True,
            "workflowFailureMode": "NoNewCalls"
        }

        request = "https://api.firecloud.org/api/workspaces/"
        request += workspace_dict['namespace'] + '/' + workspace_dict['name'] + '/' + 'submissions'
        return requests.post(request, headers=headers, data=json.dumps(payload))

    @staticmethod
    def get_workspaces(headers):
        request = "https://api.firecloud.org/api/workspaces"
        return requests.get(request, headers=headers)


class Launch(object):
    @staticmethod
    def registration(headers):
        if FireCloud.check_registration(headers).ok:
            return dict_manager.StatusDict.return_success()
        else:
            return dict_manager.StatusDict.return_danger()

    @staticmethod
    def check_billing(headers):
        r = FireCloud.get_billing_projects(headers)
        if r.ok & len(r.json()) > 0:
            return dict_manager.StatusDict.return_success()
        else:
            return dict_manager.StatusDict.return_danger()

    @classmethod
    def update_status_dict(cls, dict, token):
        headers = FireCloud.generate_headers(token)
        dict['google_status'] = dict_manager.StatusDict.return_success()
        dict['firecloud_status'] = cls.registration(headers)
        dict['billing_status'] = cls.check_billing(headers)
        return dict

    @classmethod
    def get_email(cls, headers):
        r = GCloud.get_email(headers)
        return r.json()['email']

    @classmethod
    def update_user_dict(cls, dict, token):
        headers = GCloud.generate_headers(token)
        dict['email'] = cls.get_email(headers)
        dict['username'] = dict_manager.UserDict.extract_username(dict['email'])
        return dict

    @staticmethod
    def append_workflow_id(headers, workspace):
        r = FireCloud.get_monitor_submission(headers, workspace['namespace'],
                                             workspace['name'], workspace['submissionId'])
        return dict_manager.Submission.extract_workflow_id(r.json())

    @classmethod
    def list_workspaces(cls, token):
        headers = FireCloud.generate_headers(token)
        workspaces = FireCloud.get_workspaces(headers)
        table = dict_manager.PatientTable.generate(workspaces.json())
        for idx in table.index:
            table.loc[idx, 'workflowId'] = cls.append_workflow_id(headers, table.loc[idx, :])
            table.loc[idx, 'reportUrl'] = dict_manager.PatientTable.create_report_url(
                table.loc[idx, 'bucketName'], table.loc[idx, 'submissionId'],
                table.loc[idx, 'workflowId'], table.loc[idx, 'patientId'])
        return table

    @classmethod
    def list_billing_projects(cls, token):
        headers = FireCloud.generate_headers(token)
        projects = FireCloud.get_billing_projects(headers)
        return dict_manager.BillingProjects.extract_as_tuples(projects.json())

    @staticmethod
    def create_new_workspace(token, patient):
        headers = FireCloud.generate_headers(token)
        workspace_json = dict_manager.NewWorkspace.populate_json(patient)
        new_workspace_request = FireCloud.create_new_workspace(headers, workspace_json)
        new_workspace_dict = new_workspace_request.json()
        new_workspace_dict['bucketHandle'] = dict_manager.NewWorkspace.create_gsBucket_address(
            new_workspace_dict['bucketName'])
        return new_workspace_dict

    @staticmethod
    def submit_bucket_upload(bucket, patient):
        handles = ['snvHandle', 'indelHandle', 'segHandle', 'fusionHandle',
                   'burdenHandle', 'germlineHandle', 'dnarnaHandle']
        for handle in handles:
            if patient[handle] != '':
                GCloud.upload_to_bucket(bucket, patient[handle])

    @staticmethod
    def update_datamodel(token, patient, workspace_dict):
        participant_tsv = dict_manager.DataModel.create_participant_tsv(patient)
        sample_tsv = dict_manager.DataModel.create_sample_tsv(patient)
        pair_tsv = dict_manager.DataModel.create_pair_tsv(patient, workspace_dict)

        headers = FireCloud.generate_headers(token)
        r = FireCloud.post_entities(headers, workspace_dict, participant_tsv)
        r = FireCloud.post_entities(headers, workspace_dict, sample_tsv)
        r = FireCloud.post_entities(headers, workspace_dict, pair_tsv)

    @staticmethod
    def copy_method(token, workspace_dict):
        headers = FireCloud.generate_headers(token)
        FireCloud.copy_method(headers, workspace_dict)

    @staticmethod
    def submit_method(token, patient, workspace_dict):
        headers = FireCloud.generate_headers(token)
        submission = FireCloud.post_method_submission(headers, patient, workspace_dict)
        submission_id = dict_manager.Submission.extract_submission_id(submission.json())
        attributes_tsv = dict_manager.Submission.create_attributes_tsv(submission_id)
        FireCloud.post_attributes(headers, workspace_dict, attributes_tsv)

    @classmethod
    def submit_patient(cls, credentials, patient):
        token = credentials.token
        workspace_dict = cls.create_new_workspace(token, patient)
        bucket = GCloud.initialize_bucket(credentials, workspace_dict)
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
