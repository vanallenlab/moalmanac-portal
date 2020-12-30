import configparser

default_config = 'config.ini'


def create_config():
    config = configparser.ConfigParser()
    config.read(default_config)
    return config


CONFIG = create_config()

SCOPES = ['https://www.googleapis.com/auth/cloud-platform',
          'https://www.googleapis.com/auth/userinfo.email',
          ]
