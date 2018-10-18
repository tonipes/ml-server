#!/bin/bash

gunicorn -c gunicorn_config.py app:app --reload --log-level debug
