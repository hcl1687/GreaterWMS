#!/bin/bash
export GREATERWMS_ENV=prod
python3 manage.py makemigrations
python3 manage.py migrate
supervisord -c /etc/supervisor/supervisord.conf
