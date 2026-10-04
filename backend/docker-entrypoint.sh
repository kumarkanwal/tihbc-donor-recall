#!/bin/sh
set -eu

python -m app.core.wait_for_postgres
python -m app.core.run_migrations

exec "$@"
