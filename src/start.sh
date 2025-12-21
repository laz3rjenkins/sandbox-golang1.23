#!/bin/bash
gunicorn --bind 0:9010 app.main:app --reload -w ${GUNICORN_WORKERS:=1}