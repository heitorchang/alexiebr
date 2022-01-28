#!/bin/bash

source /home/protected/venvdj32/bin/activate
gunicorn alexiebr.wsgi
