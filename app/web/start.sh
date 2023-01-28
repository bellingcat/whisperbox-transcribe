#! /usr/bin/env bash

set -e

# run migrations
alembic upgrade head

# start app
uvicorn app.web.main:app --reload --host ${HOST:-0.0.0.0} --port ${PORT:-80} --log-level info
