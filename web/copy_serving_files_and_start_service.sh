#!/bin/bash

sudo cp moalmanac-portal.service /etc/systemd/system/moalmanac-portal.service
sudo systemctl start moalmanac-portal
sudo systemctl enable moalmanac-portal

sudo cp moalmanac-portal /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/moalmanac-portal /etc/nginx/sites-enabled
sudo systemctl restart nginx
