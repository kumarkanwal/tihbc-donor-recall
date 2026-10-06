#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
ENV_FILE="$PROJECT_DIR/.env.production"
BACKUP_DIR=${BACKUP_DIR:-/var/backups/tihbc}
RETENTION_DAYS=7
retention_mtime=$((RETENTION_DAYS - 1))

umask 077
mkdir -p "$BACKUP_DIR"
LOG_FILE="$BACKUP_DIR/backup.log"
exec >>"$LOG_FILE" 2>&1

timestamp=$(date -u +%Y%m%dT%H%M%SZ)
database_backup="$BACKUP_DIR/tihbc-db-$timestamp.dump"
media_backup="$BACKUP_DIR/tihbc-media-$timestamp.tar.gz"
database_partial="$database_backup.partial"
media_partial="$media_backup.partial"

compose() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

finish() {
  status=$?
  trap - EXIT HUP INT TERM
  rm -f "$database_partial" "$media_partial"
  if [ "$status" -ne 0 ]; then
    printf '[%s] Backup failed with status %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$status"
  fi
  exit "$status"
}

trap finish EXIT
trap 'exit 1' HUP INT TERM

printf '[%s] Starting TIHBC backup\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
[ -f "$ENV_FILE" ] || { printf 'Missing environment file: %s\n' "$ENV_FILE"; exit 1; }

compose exec -T tihbc-db sh -c \
  'pg_dump --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" --format=custom --no-owner --no-privileges' \
  >"$database_partial"
mv "$database_partial" "$database_backup"

compose exec -T tihbc-api tar -C /data/media -czf - . >"$media_partial"
mv "$media_partial" "$media_backup"

find "$BACKUP_DIR" -type f \
  \( -name 'tihbc-db-*.dump' -o -name 'tihbc-media-*.tar.gz' \) \
  -mtime +"$retention_mtime" -delete

printf '[%s] Backup complete: %s, %s\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  "$(basename "$database_backup")" \
  "$(basename "$media_backup")"
