import dataset
import moment

class connect_db(object):
    path = 'submissions.db'
    table = 'submissions'

    @classmethod
    def connect(cls):
        return dataset.connect(cls.path)

    @staticmethod
    def return_table(db):
        return db[table]

class timestamp(object):
    @staticmethod
    def get_moment():
        return moment.now()

    @staticmethod
    def get_year(now):
        return now.format('YYYY')

    @staticmethod
    def get_month(now):
        return now.format('M')

    @staticmethod
    def get_day(now):
        return now.format('D')

    @staticmethod
    def get_hour(now):
        return now.format('H')

    @staticmethod
    def get_minute(now):
        return now.format('m')

    @staticmethod
    def get_second(now):
        return now.format('s')

class append_db():
    @classmethod
    def format_dict(cls, email, now):
        return {'email': email,
                'year': timestamp.get_year(now), 'month': timestamp.get_month(now), 'day': timestamp.get_day(now),
                'hour': timestamp.get_hour(now), 'minute': timestamp.get_minute(now), 'second': timestamp.get_second(now)
                }

    @staticmethod
    def append_table(table, dict):
        table.insert(dict)

    @classmethod
    def record(cls, email):
        now = timestamp.get_moment()
        dict = format.dict(email, now)

        db = connect_db.connect()
        table = connect_db.return_table(db)
        cls.append_table(table, dict)