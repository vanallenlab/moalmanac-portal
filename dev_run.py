import os
from app import app as application

if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    application.run('localhost', 8080, debug=True, ssl_context=('cert.pem', 'key.pem'))
