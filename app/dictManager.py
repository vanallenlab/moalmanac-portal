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