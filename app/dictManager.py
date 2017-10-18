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

