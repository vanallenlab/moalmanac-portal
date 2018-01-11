import os
import sqlite3
import dataset
import moment

class ConnectDb(object):
    path = 'sqlite:///submissions.db'
    table = 'submissions'

    @classmethod
    def connect(cls):
        return dataset.connect(cls.path)

    @classmethod
    def return_table(cls, db):
        return db[cls.table]

    @classmethod
    def create_new_db(cls):
        conn = sqlite3.connect(cls.path)
        conn.close()

class TimeStamp(object):
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

class AppendDb(object):
    @classmethod
    def format_dict(cls, email, now):
        return {'email': email,
                'year': TimeStamp.get_year(now), 'month': TimeStamp.get_month(now), 'day': TimeStamp.get_day(now),
                'hour': TimeStamp.get_hour(now), 'minute': TimeStamp.get_minute(now), 'second': TimeStamp.get_second(now)
                }

    @staticmethod
    def append_table(table, dict):
        table.insert(dict)

    @classmethod
    def record(cls, email):
        now = TimeStamp.get_moment()
        dict = cls.format_dict(email, now)

        if os.path.isfile(ConnectDb.path):
            ConnectDb.create_new_db()

        db = ConnectDb.connect()
        table = ConnectDb.return_table(db)
        cls.append_table(table, dict)

class ReadDb(object):
    @staticmethod
    def printDb():
        db = ConnectDb.connect()
        for submission in db['submissions']:
            print(submission)
