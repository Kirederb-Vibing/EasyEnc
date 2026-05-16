#!/bin/bash
set -e
exec python3 manage.py rqworker default
