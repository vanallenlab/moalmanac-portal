import requests
import json

from google.cloud import storage
import google.oauth2.credentials

from .dictManager import dataModelDict, statusDict, workspaceDict, submissionDict, patientTable

class firecloud_requests(object):
    @staticmethod
    def generate_headers(access_token):
        return {"Authorization" : "bearer " + str(access_token)}

    @staticmethod
    def get_health():
        return requests.get("https://api.firecloud.org/health").ok

    @staticmethod
    def check_fc_registration(headers):
        return requests.get("https://api.firecloud.org/me", headers=headers).ok

    @staticmethod
    def check_billing_projects(headers):
        return requests.get("https://api.firecloud.org/api/profile/billing", headers=headers).ok

    @staticmethod
    def get_billing_projects(headers):
        return requests.get("https://api.firecloud.org/api/profile/billing", headers=headers).json()

    @staticmethod
    def create_new_workspace(headers, json):
        return requests.post("https://api.firecloud.org/api/workspaces", headers=headers, json=json)

    @staticmethod
    def post_entities(headers, workspace_dict, entities_tsv):
        entities = {"entities": entities_tsv}
        request = "https://api.firecloud.org/api/workspaces/"
        request += workspace_dict['namespace'] + "/" + workspace_dict['name'] + "/importEntities"
        return requests.post(request, headers=headers, data=entities)

    @staticmethod
    def post_attributes(headers, workspace_dict, attributes_tsv):
        headers["content-type"] = "application/x-www-form-urlencoded"
        attributes = {'attributes': attributes_tsv}
        request = "https://api.firecloud.org/api/workspaces/"
        request += workspace_dict['namespace'] + '/' + workspace_dict['name'] + '/importAttributesTSV'
        return requests.post(request, headers=headers, data=attributes)

    @staticmethod
    def copy_method(headers, workspace_dict):
        headers["content-type"] = "application/json"
        payload = {
            "configurationNamespace": "breardon",
            "configurationName": "chips",
            "configurationSnapshotId": 45,
            "destinationNamespace": "breardon",
            "destinationName": "chips"}

        request = "https://api.firecloud.org/api/workspaces/"
        request += workspace_dict['namespace'] + '/' + workspace_dict['name'] + '/' + 'method_configs/copyFromMethodRepo'
        return requests.post(request, headers=headers, data=json.dumps(payload))

    @staticmethod
    def post_method_submission(headers, workspace_dict, patient):
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
        r = requests.post(request, headers=headers, data=json.dumps(payload))
        return submissionDict.extractSubmissionId(r)

    @staticmethod
    def get_monitor_submission(headers, namespace, name, submissionId):
        request = "https://api.firecloud.org/api/workspaces/"
        request += namespace + '/' + name + '/'
        request += 'submissions/' + submissionId
        r = requests.get(request, headers=headers)
        return submissionDict.extractWorkflowId(r)

    @staticmethod
    def get_workspaces(headers):
        return requests.get("https://api.firecloud.org/api/workspaces", headers=headers)

class gcloud_requests(object):
    @staticmethod
    def revoke_token(access_token):
        return requests.post('https://accounts.google.com/o/oauth2/revoke',
                      params={'token': access_token},
                      headers={'content-type': 'application/x-www-form-urlencoded'})

    @staticmethod
    def generate_credentials(access_token):
        credentials = google.oauth2.credentials.Credentials(access_token)
        return credentials

    @classmethod
    def initialize_bucket(cls, workspace_dict, credentials):
        credentials = google.oauth2.credentials.Credentials(access_token)
        gcs = storage.Client(credentials=credentials)
        bucket = gcs.get_bucket(workspace_dict['bucketHandle'].split('/')[2])
        return bucket

    @classmethod
    def upload_file(cls, gsBucket, file, credentials):
        blob = gsBucket.blob(file.filename)
        blob.upload_from_string(
            file.read(),
            content_type=file.content_type
        )

    @classmethod
    def upload_inputs(cls, patient, workspace_dict, access_token):
        credentials = cls.generate_credentials(access_token)
        gsBucket = cls.initialize_bucket(workspace_dict, credentials)
        handles = ['snvHandle', 'indelHandle', 'segHandle', 'fusionHandle',
                   'burdenHandle', 'germlineHandle', 'dnarnaHandle']
        for handle_ in handles:
            if patient[handle_].filename != '':
                cls.upload_file(gsBucket, patient[handle_], credentials)

class process_requests(firecloud_requests):
    @staticmethod
    def list_billing_projects(billing_projects_json):
        list_ = []
        for project_ in billing_projects_json:
            list_.extend([str(project_['projectName'])])
        return list_

class launch_requests(object):
    @staticmethod
    def launch_check_fc_registration(access_token):
        headers = firecloud_requests.generate_headers(access_token)
        if firecloud_requests.check_fc_registration(headers):
            return statusDict.return_success()
        else:
            return statusDict.return_danger()

    @staticmethod
    def launch_check_billing_projects(access_token):
        headers = firecloud_requests.generate_headers(access_token)
        if firecloud_requests.check_billing_projects(headers):
            json = firecloud_requests.get_billing_projects(headers)
            if len(json) > 0:
                return statusDict.return_success()
            else:
                return statusDict.return_danger()
        else:
            return statusDict.return_danger()

    @staticmethod
    def launch_list_billing_projects(access_token):
        headers = firecloud_requests.generate_headers(access_token)
        json = firecloud_requests.get_billing_projects(headers)
        return process_requests.list_billing_projects(json)

    @staticmethod
    def launch_list_workspaces(access_token):
        headers = firecloud_requests.generate_headers(access_token)
        workspaces = firecloud_requests.get_workspaces(headers)
        workspaces_json = workspaces.json()
        return patientTable.generate_patientTable(workspaces_json, headers)

    @staticmethod
    def launch_create_new_workspace(access_token, patient):
        headers = firecloud_requests.generate_headers(access_token)
        json = workspaceDict.populate_workspace_json(patient)
        workspace = firecloud_requests.create_new_workspace(headers, json)
        workspace_dict = workspaceDict.populate_gsBucket(workspace)
        return workspace_dict

    @staticmethod
    def launch_upload_to_googleBucket(patient, workspace_dict, access_token):
        gcloud_requests.upload_inputs(patient, workspace_dict, access_token)

    @staticmethod
    def launch_update_datamodel(access_token, patient, workspace_dict):
        participant_tsv = dataModelDict.create_participant_tsv(patient)
        sample_tsv = dataModelDict.create_sample_tsv(patient)
        pair_tsv = dataModelDict.create_pair_tsv(patient, workspace_dict)

        headers = firecloud_requests.generate_headers(access_token)
        firecloud_requests.post_entities(headers, workspace_dict, participant_tsv)
        firecloud_requests.post_entities(headers, workspace_dict, sample_tsv)
        firecloud_requests.post_entities(headers, workspace_dict, pair_tsv)

    @staticmethod
    def launch_copy_method(access_token, workspace_dict):
        headers = firecloud_requests.generate_headers(access_token)
        firecloud_requests.copy_method(headers, workspace_dict)

    @staticmethod
    def launch_method_submission(access_token, workspace_dict, patient):
        headers = firecloud_requests.generate_headers(access_token)
        submissionId = firecloud_requests.post_method_submission(headers, workspace_dict, patient)
        #workflowId = firecloud_requests.get_monitor_submission(headers, workspace_dict, submissionId)
        attributesTsv = submissionDict.create_attributesTsv(submissionId)
        firecloud_requests.post_attributes(headers, workspace_dict, attributesTsv)

    @classmethod
    def launch_csPortal(cls, access_token, patient):
        workspace_dict = cls.launch_create_new_workspace(access_token, patient)
        cls.launch_upload_to_googleBucket(patient, workspace_dict, access_token)
        cls.launch_update_datamodel(access_token, patient, workspace_dict)
        cls.launch_copy_method(access_token, workspace_dict)
        cls.launch_method_submission(access_token, workspace_dict, patient)

class firecloud_functions(object):
    @staticmethod
    def evaluate_upload_status(status_dict):
        if 'danger' not in status_dict.values():
            return True
        else:
            return False

    @staticmethod
    def populate_status(dict, access_token):
        dict['google_status'] = statusDict.return_success()
        dict['firecloud_status'] = launch_requests.launch_check_fc_registration(access_token)
        dict['billing_status'] = launch_requests.launch_check_billing_projects(access_token)
        return dict

    @staticmethod
    def populate_user(dict, access_token):
        billing_list = launch_requests.launch_list_billing_projects(access_token)
        dict['firecloud_billing'] = []
        for i in range(0, len(billing_list)):
            dict['firecloud_billing'].append(tuple([billing_list[i], billing_list[i]]))
        return dict
