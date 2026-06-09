#!/bin/bash

pip install -r requirements.txt
python3 manage.py runserver &
sleep 2
xdg-open http://127.0.0.1:8000/
fg