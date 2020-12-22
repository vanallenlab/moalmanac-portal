# Useful scripts for the web host

Scripts in this directory are used to serve the application on a Google Compute Engine VM.

## Installation
Run `copy_serving_files_and_start_service.sh` to configure gunicorn and nginx. Check [this guide](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04) for additional steps, such as creating a https certificate.

## View logs
- `project_log_view.sh` to view the system log for project
- `nginx_view.sh` to view nginx process logs
- `nginx_view_access.sh` to view nginx access logs
- `nginx_view_error.sh` to view nginx error logs
