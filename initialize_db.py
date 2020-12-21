import sqlite3

from app import db


def initialize():
    try:
        db.init_db_command()
    except sqlite3.OperationalError:
        print("db exists")
        pass


if __name__ == "__main__":
    initialize()
