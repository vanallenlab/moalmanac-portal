import io
import pandas as pd
import dateutil.parser as parser
import json

from datetime import datetime
from datetime import timedelta

from config import CONFIG


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


class Credentials(object):
    @staticmethod
    def for_google(user, secrets):
        return {
            'token': user.access_token,
            'refresh_token': user.refresh_token,
            'token_uri': secrets['web']['token_uri'],
            'client_id': secrets['web']['client_id'],
            'client_secret': secrets['web']['client_secret'],
            'scopes': user.scopes.split(' ')
        }

    @staticmethod
    def json_to_dictionary(content):
        return json.loads(content)


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

    @staticmethod
    def convert_content_to_dataframe(response_content):
        return pd.read_csv(io.BytesIO(response_content), encoding='utf-8', sep='\t')


class DateTime(object):
    dt_format = '%Y-%m-%d_%H:%M:%S'

    @classmethod
    def dt_to_str(cls, dt):
        return dt.strftime(cls.dt_format)

    @classmethod
    def str_to_dt(cls, dt_str):
        return datetime.strptime(dt_str, cls.dt_format)

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
    def time_to_renew_token(cls, time_authorized):
        delta_t = cls.calculate_delta_t(time_authorized)
        return delta_t >= timedelta(seconds=3500)


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


class Oncotree(object):
    # http://oncotree.mskcc.org/oncotree/#/home oncotree_2017_06_21
    oncotree_path = 'app/static/files/oncotree_dict.txt'

    @classmethod
    def create_oncotree(cls):
        tumor_type_list = cls.return_tumor_types()
        return sorted([str(ontology) for ontology in tumor_type_list])
        #ontology_list = []
        #for ontology in tumor_type_list:
        #    ontology_list.append(str(ontology))
        #return ontology_list

    @classmethod
    def extract_shortcode(cls, ontology):
        oncotree = cls.return_tumor_types()
        if ontology in oncotree:
            shortcode = str(ontology).split('(')[1].split(')')[0]
            return str(shortcode)
        else:
            return ontology

    @classmethod
    def extract_longcode(cls, ontology):
        oncotree = cls.return_tumor_types()
        if ontology in oncotree:
            longcode = str(ontology).split(' (')[0]
            return str(longcode)
        else:
            return ontology

    @classmethod
    def import_oncotree(cls):
        return pd.read_csv(cls.oncotree_path, sep='\t')

    @classmethod
    def return_tumor_types(cls):
        df = cls.import_oncotree()
        return df['tumorType'].tolist()


class PatientTable(object):
    patient_table_cols = ['namespace', 'name', 'url', 'time', 'createdDate', 'tumorTypeShort', 'tumorTypeLong',
                          'patientId', 'description', 'runningJobs', 'completed']
    something_went_wrong = '?'

    @staticmethod
    def convert_time(created_date):
        return parser.parse(created_date)

    @staticmethod
    def create_report_blob(submission_id, workflow_id, patient_id):
        subfolder1 = 'MolecularOncologyAlmanac'
        subfolder2 = 'call-almanacTask'
        return '{}/{}/{}/{}/{}.report.html'.format(submission_id, subfolder1, workflow_id, subfolder2, patient_id)

    @staticmethod
    def create_report_url(bucket_name, submission_id, workflow_id, patient_id):
        url = "https://api.firecloud.org/cookie-authed/download/b/" + bucket_name + "/o/" + submission_id + "/CHIPS/"
        url += workflow_id + "/call-chipsTask/" + patient_id + ".report.html"
        return url

    @staticmethod
    def create_workspace_url(namespace, name):
        return f"https://app.terra.bio/#workspaces/{namespace}/{name}"

    @classmethod
    def format_workspace(cls, workspace):
        workspace_values = workspace['workspace']
        namespace = workspace_values['namespace']
        name = workspace_values['name']
        bucket_name = workspace_values['bucketName']
        created_date = workspace_values['createdDate']
        attributes = workspace_values['attributes']
        submission = workspace['workspaceSubmissionStats']

        tumor_type_short = cls.return_attribute(attributes, 'tumorTypeShort', upper=True)
        tumor_type_long = cls.return_attribute(attributes, 'tumorTypeLong', upper=True)
        patient_id = cls.return_attribute(attributes, 'patientId')
        description = cls.return_attribute(attributes, 'description')
        submission_id = cls.return_attribute(attributes, 'submissionId')

        df = pd.DataFrame(columns=cls.patient_table_cols)
        df.loc[0, 'namespace'] = str(namespace)
        df.loc[0, 'name'] = str(name)
        df.loc[0, 'url'] = cls.create_workspace_url(namespace, name)
        df.loc[0, 'bucketName'] = str(bucket_name)
        df.loc[0, 'createdDate'] = str(created_date)
        df.loc[0, 'time'] = cls.convert_time(str(created_date))
        df.loc[0, 'tumorTypeShort'] = tumor_type_short
        df.loc[0, 'tumorTypeLong'] = tumor_type_long
        df.loc[0, 'patientId'] = patient_id
        df.loc[0, 'description'] = description
        df.loc[0, 'runningJobs'] = submission['runningSubmissionsCount']
        df.loc[0, 'completed'] = 'lastSuccessDate' in submission.keys()
        df.loc[0, 'workflowId'] = ''
        df.loc[0, 'reportUrl'] = ''
        df.loc[0, 'submissionId'] = submission_id
        return df

    @classmethod
    def generate(cls, all_workspaces_json):
        tagged_workspaces = cls.subset_tagged_workspaces(all_workspaces_json)
        portal_workspaces = cls.subset_portal_workspaces(tagged_workspaces)

        patient_table = pd.DataFrame(columns=cls.patient_table_cols)
        for workspace in portal_workspaces:
            patient_table = patient_table.append(cls.format_workspace(workspace), ignore_index=True)
        return patient_table.sort_values(by='createdDate', ascending=False)

    @classmethod
    def return_attribute(cls, dictionary, string, upper=False):
        if upper:
            return dictionary[string].upper() if string in list(dictionary.keys()) else cls.something_went_wrong
        else:
            return dictionary[string] if string in list(dictionary.keys()) else cls.something_went_wrong

    @staticmethod
    def return_items(workspace_dictionary):
        return workspace_dictionary['workspace']['attributes']['tag:tags']['items']

    @staticmethod
    def subset_tagged_workspaces(all_workspaces):
        return [workspace for workspace in all_workspaces if "tag:tags" in workspace['workspace']['attributes']]

    @classmethod
    def subset_portal_workspaces(cls, tagged_workspaces):
        app_tag = CONFIG['STRINGS']['APP_TAG']
        return [workspace for workspace in tagged_workspaces if app_tag in cls.return_items(workspace)]


class Status(object):
    SUCCESS = "success"
    DANGER = "danger"

    GOOGLE = 'google'
    TERRA = 'terra'
    BILLING = 'billing'

    @classmethod
    def new_dict(cls):
        return {cls.GOOGLE: cls.DANGER, cls.TERRA: cls.DANGER, cls.BILLING: cls.DANGER}

    @classmethod
    def evaluate(cls, dictionary):
        if cls.DANGER not in dictionary.values():
            return True
        else:
            return False

    @classmethod
    def update(cls, dictionary, registered, billing, credentials):
        dictionary[cls.GOOGLE] = cls.SUCCESS
        for status_code, key in [(registered, cls.TERRA), (billing, cls.BILLING)]:
            if status_code == 200:
                new_value = cls.SUCCESS
            else:
                new_value = cls.DANGER
            dictionary[key] = new_value

        for key, value in credentials.items():
            dictionary[key] = value
        return dictionary


class Submission(object):
    @staticmethod
    def extract_workflow_id(workflow):
        if 'workflows' in list(workflow.keys()):
            if 'workflowId' in list(workflow['workflows'][0].keys()):
                return str(workflow['workflows'][0]['workflowId'])
            return ''
        return ''

    @staticmethod
    def extract_submission_id(workflow):
        if 'submissionId' in list(workflow.keys()):
            return str(workflow['submissionId'])
        else:
            return ''

    @staticmethod
    def create_attributes_tsv(submission_id):
        return pd.DataFrame({'workspace:submissionId': submission_id}, index=[0]).to_csv(sep='\t', index=False)


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
                "tag:tags": {u'items': [u'{}'.format(CONFIG['STRINGS']['APP_TAG'])], u'itemsType': u'AttributeValue'},
                "patientId": str(patient['patientId']),
                "tumorTypeShort": str(patient['tumorTypeShort']),
                "tumorTypeLong": str(patient['tumorTypeLong'])},
            "authorizedDomain": []
        }

    @staticmethod
    def create_gsBucket_address(bucketName):
        return "gs://" + bucketName + "/"

    @staticmethod
    def extract_bucket_handle(workspace_dictionary):
        return workspace_dictionary['bucketHandle'].split('/')[2]
