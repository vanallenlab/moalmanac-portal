import pandas as pd
from datetime import datetime

class statusDict(object):
    @staticmethod
    def new_dict():
        return {'google_status': 'danger', 'firecloud_status': 'danger', 'billing_status': 'danger'}

    @staticmethod
    def return_success():
        return "success"

    @staticmethod
    def return_danger():
        return "danger"

class userDict(object):
    @staticmethod
    def new_dict():
        return {'userinfo': '', 'email': '', 'user': ''}

    @staticmethod
    def populate_googleauth(dict, google):
        dict['userinfo'] = google.get('userinfo')
        dict['email'] = dict['userinfo'].data['email']
        dict['user'] = dict['email'].split('@')[0]
        return dict

class workspaceDict(object):
    @staticmethod
    def format_workspace_description(description):
        return unicode(description.replace("\r\n", "\n"))

    @staticmethod
    def to_str(notstring):
        return str(notstring)

    @classmethod
    def create_workspace_name(cls, patient):
        name = cls.to_str(patient['tumorType']) + '_'
        name += cls.to_str(patient['patientId']) + '_'
        name += cls.to_str(datetime.now().strftime('%Y-%m-%d')) + '_'
        name += cls.to_str(datetime.now().strftime('%H-%M-%S'))
        return name

    @classmethod
    def populate_workspace_json(cls, patient):
        json = {
            "namespace": cls.to_str(patient['billingProject']),
            "name": cls.create_workspace_name(patient),
            "attributes": {
                "description": cls.format_workspace_description(patient['description']),
                "tag:tags": {u'items': [u'Chips&SalsaPortal'], u'itemsType': u'AttributeValue'},
                "patientId": cls.to_str(patient['patientId']),
                "tumorType": cls.to_str(patient['tumorType'])
            },
            "authorizedDomain": []
        }
        return json

    @classmethod
    def populate_gsBucket(cls, workspace):
        json = workspace.json()
        json['bucketId'] = str(json['bucketName'])
        json['bucketHandle'] = 'gs://' + json['bucketId'] + '/'
        return json

class dataModelDict(object):
    @staticmethod
    def df_to_str(df):
        return df.to_csv(sep='\t', index=False)

    @staticmethod
    def tsv_to_entities_dict(entities_tsv):
        return {"entities": entities_tsv}

    @classmethod
    def create_participant_tsv(cls, patient):
        patientId = patient['patientId']
        disease = patient['tumorType']
        df = pd.DataFrame(columns=['entity:participant_id', 'disease'], index=[0])
        df.loc[0, 'entity:participant_id'] = patientId
        df.loc[0, 'disease'] = disease
        return cls.df_to_str(df)

    @classmethod
    def create_sample_tsv(cls, patient):
        tumor_sample = patient['patientId'] + '-tumor'
        normal_sample = patient['patientId'] + '-normal'

        _columns = ['entity:sample_id', 'participant_id']
        df = pd.DataFrame(columns=_columns)

        df.loc[0, 'entity:sample_id'] = tumor_sample
        df.loc[1, 'entity:sample_id'] = normal_sample
        df.loc[:, 'participant_id'] = patient['patientId']
        df.loc[:, 'disease'] = patient['tumorType']
        return cls.df_to_str(df)

    @classmethod
    def create_pair_tsv(cls, patient, workspace_dict):
        _columns = ['entity:pair_id', 'participant_id', 'case_sample', 'control_sample',
                    'snvHandle', 'indelHandle', 'segHandle', 'fusionHandle',
                    'burdenHandle', 'germlineHandle', 'dnarnaHandle']
        df = pd.DataFrame(columns=_columns, index=[0])
        tumor_sample = patient['patientId'] + '-tumor'
        normal_sample = patient['patientId'] + '-normal'
        google_bucket = workspace_dict['bucketHandle']

        df.loc[0, 'entity:pair_id'] = patient['patientId'] + '-pair'
        df.loc[0, 'participant_id'] = patient['patientId']
        df.loc[0, 'case_sample'] = tumor_sample
        df.loc[0, 'control_sample'] = normal_sample

        for column_ in _columns[4:]:
            if patient[column_].filename != '':
                df.loc[0, column_] = google_bucket + patient[column_].filename
        df_tsv = cls.df_to_str(df)
        return cls.tsv_to_entities_dict(df_tsv)