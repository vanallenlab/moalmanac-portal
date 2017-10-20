import requests
import firecloud.api as fcapi

from google.cloud import storage
from dictManager import dataModelDict, statusDict, workspaceDict

class firecloud_requests(object):
    # https://api.firecloud.org/
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
    def post_entities(workspace_dict, entities_tsv):
        fcapi.upload_entities(namespace=workspace_dict['namespace'],
                              workspace=workspace_dict['name'],
                              entity_data=entities_tsv)

class gcloud_requests(object):
    @staticmethod
    def initialize_bucket(workspace_dict):
        gcs = storage.Client()
        bucket = gcs.get_bucket(workspace_dict['bucketHandle'].split('/')[2])
        return bucket

    @staticmethod
    def upload_file(gsBucket, file):
        blob = gsBucket.blob(file.filename)
        blob.upload_from_string(
            file.read(),
            content_type=file.content_type
        )

    # To Do: Make a progress bar or status update
    @classmethod
    def upload_inputs(cls, patient, workspace_dict):
        gsBucket = cls.initialize_bucket(workspace_dict)
        handles = ['snvHandle', 'indelHandle', 'segHandle', 'fusionHandle',
                   'burdenHandle', 'germlineHandle', 'dnarnaHandle']
        for handle_ in handles:
            if patient[handle_].filename != '':
                cls.upload_file(gsBucket, patient[handle_])

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
    def launch_create_new_workspace(access_token, patient):
        headers = firecloud_requests.generate_headers(access_token)
        json = workspaceDict.populate_workspace_json(patient)
        workspace = firecloud_requests.create_new_workspace(headers, json)
        workspace_dict = workspaceDict.populate_gsBucket(workspace)
        return workspace_dict

    @staticmethod
    def launch_upload_to_googleBucket(patient, workspace_dict):
        gcloud_requests.upload_inputs(patient, workspace_dict)

    @staticmethod
    def launch_update_datamodel(patient, workspace_dict):
        participant_tsv = dataModelDict.create_participant_tsv(patient)
        sample_tsv = dataModelDict.create_sample_tsv(patient)
        pair_tsv = dataModelDict.create_pair_tsv(patient, workspace_dict)

        firecloud_requests.post_entities(workspace_dict, participant_tsv)
        firecloud_requests.post_entities(workspace_dict, sample_tsv)
        firecloud_requests.post_entities(workspace_dict, pair_tsv)

    @classmethod
    def launch_csPortal(cls, access_token, patient):
        workspace_dict = cls.launch_create_new_workspace(access_token, patient)
        cls.launch_upload_to_googleBucket(patient, workspace_dict)
        cls.launch_update_datamodel(patient, workspace_dict)

# Should rename this firecloud_requests
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

