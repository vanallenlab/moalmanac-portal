# Molecular Oncology Almanac portal
The Molecular Oncology Almanac portal is developed with [Flask](https://flask.palletsprojects.com/) and served with Gunicorn and Nginx on an Ubuntu 18.04 Google Compute Engine VM. [This guide by Digital Ocean](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04) was largely followed.

## Installation
The Molecular Oncology Almanac portal uses Python 3.7. It is recommended that users create a virtual environment. 

```bash
conda create -y -n moalmanac-portal python=3.7
conda activate moalmanac-portal
pip install -r requirements.txt
```

For development, launch the application with `dev_run.py` and use `run.py` for production. Create a [self-signed certificate](https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https) to pass `key.pem` and `cert.pem` in order to develop with https locally.
