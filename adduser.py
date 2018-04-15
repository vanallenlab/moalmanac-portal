import dataset
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--newuser', help='Email address for new admin',
                    required=True)
args = parser.parse_args()
newuser = args.newuser

TABLE = 'admin'

DB = 'sqlite:///submissions.db'
db = dataset.connect(DB)
table = db.create_table(TABLE)
table.insert(dict(email=newuser))
