import pandas as pd
import moment
import json

from datetime import datetime
from datetime import timedelta

class StatusDict(object):
    @staticmethod
    def new_dict():
        return {'google_status': 'danger', 'firecloud_status': 'danger', 'billing_status': 'danger'}

    @staticmethod
    def return_success():
        return "success"

    @staticmethod
    def return_danger():
        return "danger"

    @staticmethod
    def evaluate(dict):
        if 'danger' not in dict.values():
            return True
        else:
            return False


class UserDict(object):
    @staticmethod
    def new_dict():
        return {'email': '', 'username': ''}

    @staticmethod
    def extract_username(email):
        return email.split('@')[0]


class DateTime(object):
    dt_format = '%Y-%m-%d_%H:%M:%S'

    @classmethod
    def dt_to_str(cls, dt):
        return dt.strftime(cls.dt_format)

    @classmethod
    def str_to_dt(cls, dtstr):
        return datetime.strptime(dtstr, cls.dt_format)

    @staticmethod
    def get_datetime_now():
        return datetime.now()

    @classmethod
    def datetime_for_session(cls):
        dt_now = cls.get_datetime_now()
        return cls.dt_to_str(dt_now)

    @classmethod
    def calculate_delta_t(cls, time_authorized):
        dt_now = cls.get_datetime_now()
        dt_authorized = cls.str_to_dt(time_authorized)
        return dt_now - dt_authorized

    @classmethod
    def time_to_renew(cls, time_authorized):
        delta_t = cls.calculate_delta_t(time_authorized)
        return delta_t >= timedelta(seconds=3500)


class Credentials(object):
    @staticmethod
    def credentials_to_dict(credentials):
        return {'token': credentials.token, 'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri, 'client_id': credentials.client_id,
                'client_secret': credentials.client_secret, 'scopes': credentials.scopes}

class PatientTable(object):
    patient_table_cols = ['namespace', 'name', 'url', 'time', 'createdDate', 'tumorTypeShort', 'tumorTypeLong',
                          'patientId', 'description', 'runningJobs', 'completed']

    @staticmethod
    def subset_tagged_workspaces(all_workspaces):
        return [workspace for workspace in all_workspaces if "tag:tags" in workspace['workspace']['attributes']]

    @staticmethod
    def subset_portal_workspaces(tagged_workspaces):
        return [workspace for workspace in tagged_workspaces if u'Chips&SalsaPortal' in workspace['workspace']['attributes']['tag:tags']['items']]

    @staticmethod
    def create_workspace_url(namespace, name):
        return "https://portal.firecloud.org/#workspaces/" + str(namespace) + "/" + str(name)

    @staticmethod
    def convert_time(createdDate):
        return datetime.strptime(createdDate, "%Y-%m-%dT%H:%M:%S.%fZ")

    @staticmethod
    def create_report_url(bucket_name, submission_id, workflow_id, patient_id):
        url = "https://api.firecloud.org/cookie-authed/download/b/" + bucket_name + "/o/" + submission_id + "/CHIPS/"
        url += workflow_id + "/call-chipsTask/" + patient_id + ".report.html"
        return url

    @classmethod
    def format_workspace(cls, workspace):
        workspace_values = workspace['workspace']
        namespace = workspace_values['namespace']
        name = workspace_values['name']
        created_date = workspace_values['createdDate']
        attributes = workspace_values['attributes']
        submission = workspace['workspaceSubmissionStats']

        df = pd.DataFrame(columns=cls.patient_table_cols)
        df.loc[0, 'namespace'] = namespace
        df.loc[0, 'name'] = str(name)
        df.loc[0, 'url'] = cls.create_workspace_url(namespace, name)
        df.loc[0, 'bucketName'] = str(workspace_values['bucketName'])
        df.loc[0, 'createdDate'] = str(created_date)
        df.loc[0, 'time'] = cls.convert_time(str(created_date))
        df.loc[0, 'tumorTypeShort'] = attributes['tumorTypeShort'].upper()
        df.loc[0, 'tumorTypeLong'] = attributes['tumorTypeLong']
        df.loc[0, 'patientId'] = attributes['patientId']
        df.loc[0, 'description'] = attributes['description']
        df.loc[0, 'runningJobs'] = submission['runningSubmissionsCount']
        df.loc[0, 'completed'] = 'lastSuccessDate' in submission.keys()
        df.loc[0, 'workflowId'] = ''
        df.loc[0, 'reportUrl'] = ''

        if 'submissionId' in attributes:
            df.loc[0, 'submissionId'] = attributes['submissionId']
        else:
            df.loc[0, 'submissionId'] = ''
        return df

    @classmethod
    def generate(cls, all_workspaces_json):
        tagged_workspaces = cls.subset_tagged_workspaces(all_workspaces_json)
        portal_workspaces = cls.subset_portal_workspaces(tagged_workspaces)

        patient_table = pd.DataFrame(columns = cls.patient_table_cols)
        for workspace in portal_workspaces:
            patient_table = patient_table.append(cls.format_workspace(workspace), ignore_index=True)
        return patient_table.sort_values(['createdDate'], ascending=False)

class Oncotree(object):
    # http://oncotree.mskcc.org/oncotree/#/home oncotree_2017_06_21
    oncotree_path = 'app/static/files/oncotree_chipssalsa_dict.txt'

    @classmethod
    def import_oncotree(cls):
        return pd.read_csv(cls.oncotree_path, sep='\t')

    @classmethod
    def return_tumorTypes(cls):
        df = cls.import_oncotree()
        return df['tumorType'].tolist()

    @classmethod
    def create_oncotree(cls):
        tumorTypeList = cls.return_tumorTypes()
        list_ = []
        for ontology in tumorTypeList:
            list_.append(str(ontology))
        return list_

    @classmethod
    def extract_shortcode(cls, ontology):
        oncotree = cls.return_tumorTypes()
        if ontology in oncotree:
            shortcode = str(ontology).split('(')[1].split(')')[0]
            return str(shortcode)
        else:
            return ontology

    @classmethod
    def extract_longcode(cls, ontology):
        oncotree = cls.return_tumorTypes()
        if ontology in oncotree:
            longcode = str(ontology).split(' (')[0]
            return str(longcode)
        else:
            return ontology


class Form(object):
    @staticmethod
    def populate_patient(form):
        return {
            'billingProject': form.billingProject.data,
            'patientId': form.patientId.data,
            'tumorType': form.tumorType.data,
            'description': form.description.data,
            'snvHandle': form.snvHandle.data,
            'indelHandle': form.indelHandle.data,
            'burdenHandle': form.burdenHandle.data,
            'segHandle': form.segHandle.data,
            'fusionHandle': form.fusionHandle.data,
            'dnarnaHandle': form.dnarnaHandle.data,
            'germlineHandle': form.germlineHandle.data,
            'tumorTypeShort': Oncotree.extract_shortcode(form.tumorType.data),
            'tumorTypeLong': Oncotree.extract_longcode(form.tumorType.data)
        }


class Submission(object):
    @staticmethod
    def extract_workflow_id(workflow):
        if 'workflowId' in workflow['workflows'][0].keys():
            return str(workflow['workflows'][0]['workflowId'])
        else:
            return ''

    @staticmethod
    def extract_submission_id(workflow):
        if 'submissionId' in workflow.keys():
            return str(workflow['submissionId'])
        else:
            return ''

    @staticmethod
    def create_attributes_tsv(submission_id):
        return pd.DataFrame({'workspace:submissionId':submission_id}, index=[0]).to_csv(sep='\t', index=False)


class BillingProjects(object):
    @staticmethod
    def extract_list(billing_projects):
        list_ = []
        for project in billing_projects:
            list_.append(project['projectName'])
        return list_

    @classmethod
    def extract_as_tuples(cls, billing_projects):
        billing_projects_list = cls.extract_list(billing_projects)
        return [(billing_project, billing_project) for billing_project in billing_projects_list]

class NewWorkspace(object):
    @classmethod
    def create_workspace_name(cls, patient_id, tumor_type):
        return str(tumor_type) + '_' + str(patient_id) + '_' + str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))

    @staticmethod
    def format_workspace_description(description):
        return str(description.replace("/r/n", "/n"))

    @classmethod
    def populate_json(cls, patient):
        return {
            "namespace": str(patient['billingProject']),
            "name": cls.create_workspace_name(patient['patientId'], patient['tumorTypeShort']),
            "attributes": {
                "description": cls.format_workspace_description(patient['description']),
                "tag:tags": {u'items': [u'Chips&SalsaPortal'], u'itemsType': u'AttributeValue'},
                "patientId": str(patient['patientId']),
                "tumorTypeShort": str(patient['tumorTypeShort']),
                "tumorTypeLong": str(patient['tumorTypeLong'])},
            "authorizedDomain": []
        }

    @staticmethod
    def create_gsBucket_address(bucketName):
        return "gs://" + bucketName + "/"


class DataModel(object):
    @staticmethod
    def create_participant_tsv(patient):
        df = pd.DataFrame(columns=['entity:participant_id', 'disease'], index=[0])
        df.loc[0, 'entity:participant_id'] = patient['patientId']
        df.loc[0, 'disease'] = patient['tumorTypeShort']
        return df.to_csv(sep='\t', index=False)

    @staticmethod
    def create_sample_tsv(patient):
        df = pd.DataFrame(columns=['entity:sample_id', 'participant_id'], index=[0, 1])
        df.loc[0, 'entity:sample_id'] = patient['patientId'] + '-tumor'
        df.loc[1, 'entity:sample_id'] = patient['patientId'] + '-normal'
        df.loc[:, 'participant_id'] = patient['patientId']
        df.loc[:, 'disease'] = patient['tumorTypeShort']
        return df.to_csv(sep='\t', index=False)

    @staticmethod
    def create_pair_tsv(patient, workspace_dict):
        _columns = ['entity:pair_id', 'participant_id', 'case_sample', 'control_sample',
                    'snvHandle', 'indelHandle', 'segHandle', 'fusionHandle',
                    'burdenHandle', 'germlineHandle', 'dnarnaHandle']
        df = pd.DataFrame(columns=_columns, index=[0])
        df.loc[0, 'participant_id'] = patient['patientId']
        df.loc[0, 'entity:pair_id'] = patient['patientId'] + '-pair'
        df.loc[0, 'case_sample'] = patient['patientId'] + '-tumor'
        df.loc[0, 'control_sample'] = patient['patientId'] + '-normal'

        google_bucket = workspace_dict['bucketHandle']
        for column_ in _columns[4:]:
            if patient[column_] != '':
                df.loc[0, column_] = google_bucket + patient[column_].filename
        return df.to_csv(sep='\t', index=False)
