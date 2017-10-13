import requests
from dictManager import statusDict

class firecloud_requests(object):
    # https://api.firecloud.org/
    @staticmethod
    def generate_headers(access_token):
        return {"Authorization" : "bearer " + str(access_token)}

    @staticmethod
    def get_health():
        return requests.get("http://api.firecloud.org/health").ok

    @staticmethod
    def check_fc_registration(headers):
        return requests.get("http://api.firecloud.org/me", headers=headers).ok

    @staticmethod
    def check_billing_projects(headers):
        return requests.get("https://api.firecloud.org/api/profile/billing", headers=headers).ok

    @staticmethod
    def get_billing_projects(headers):
        return requests.get("https://api.firecloud.org/api/profile/billing", headers=headers).json()

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
