# TIHBC production runbook

This deployment serves `https://tihbc.kanwalkumar.com` from one Docker Compose project. Caddy reaches
`tihbc-web` and `tihbc-api` over the shared external `proxy` network. PostgreSQL and Redis are reachable
only on the private `tihbc-internal` network. No service publishes a host port.

Run Compose commands from the repository root with the production environment file:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml COMMAND
```

Never run `docker compose config` without `--quiet` against the real production environment because its
rendered output can contain secrets.

## First deployment

1. Clone the repository to `/opt/tihbc-donor-recall` and check out the approved release commit.
2. Confirm that the shared proxy network exists and that the Caddy container is attached to it:

   ```bash
   docker network inspect proxy
   ```

   If this is a new VPS and the network does not exist, create it once with `docker network create proxy`,
   then attach the Caddy container according to that proxy stack's own runbook.
3. Create the production environment and restrict it:

   ```bash
   cd /opt/tihbc-donor-recall
   cp .env.production.example .env.production
   chmod 600 .env.production
   ```

   Replace every `CHANGE_ME` value. `POSTGRES_PASSWORD` and the password embedded in `DATABASE_URL` must
   be identical and URL-safe. Set `CORS_ORIGINS=https://tihbc.kanwalkumar.com`, and change `JWT_SECRET`,
   `POSTGRES_PASSWORD`, and both seed passwords. Leave provider keys blank unless that provider is
   intentionally enabled. Never paste the completed file into chat, logs, or source control.
4. Refuse deployment if placeholders remain, then validate without rendering secrets:

   ```bash
   if grep -q 'CHANGE_ME' .env.production; then echo 'Replace production placeholders first'; exit 1; fi
   docker compose --env-file .env.production -f docker-compose.prod.yml config --quiet
   ```

5. Build and start the stack. The API alone applies Alembic migrations; the worker explicitly skips them.

   ```bash
   docker compose --env-file .env.production -f docker-compose.prod.yml build
   docker compose --env-file .env.production -f docker-compose.prod.yml up -d
   docker compose --env-file .env.production -f docker-compose.prod.yml ps
   ```

6. Add and validate the Caddy block using the procedure below, then seed and run the health checks.

## Caddy procedure

The Caddy container must be attached to `proxy`, and its mounted Caddyfile must be writable on the host.
Set the two example values below to the actual container name and bind-mounted host path. Append the block
only once.

```bash
CADDY_CONTAINER=caddy
CADDYFILE_HOST=/opt/caddy/Caddyfile
sudo cp --preserve=all "$CADDYFILE_HOST" "$CADDYFILE_HOST.backup.$(date -u +%Y%m%dT%H%M%SZ)"
sudo tee -a "$CADDYFILE_HOST" < deploy/caddy-tihbc.block >/dev/null
docker exec "$CADDY_CONTAINER" caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
docker exec "$CADDY_CONTAINER" caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
```

If validation fails, restore the backup and validate again. Always use `caddy reload`; never restart Caddy
for a TIHBC configuration change.

## Seed and reset demo data

Seed the complete deterministic dataset after the first successful startup:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec tihbc-api python -m app.seed
```

The command preserves staff users and the demo-clock offset while rebuilding operational demo data. It is
also the command-line reset procedure. Administrators can perform the same reset from Settings while
`DEMO_MODE=true`. Take a backup before resetting data that may be needed later.

## Update

Create a backup first and record both the current commit and database migration state:

```bash
./deploy/backup.sh
git rev-parse HEAD
docker compose --env-file .env.production -f docker-compose.prod.yml exec tihbc-api alembic current
git fetch --prune
git pull --ff-only
docker compose --env-file .env.production -f docker-compose.prod.yml build
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

Run the health checks after every update. Caddy does not need a reload unless its block changed.

## Rollback

Application rollback rebuilds the previously recorded commit:

```bash
git switch --detach PREVIOUS_COMMIT_SHA
docker compose --env-file .env.production -f docker-compose.prod.yml build
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

The API migrates forward on startup. Do not automatically downgrade a database migration. If the old app
cannot run against the upgraded schema, stop the web, worker, and API services and restore the pre-update
database and media backups as described below. After recovery, run the health checks before restoring
traffic.

## Logs and status

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
docker compose --env-file .env.production -f docker-compose.prod.yml logs --tail=200 tihbc-api tihbc-worker
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f tihbc-web tihbc-api tihbc-worker
```

Logs must not contain full donor phone numbers, credentials, tokens, or environment-file contents. Do not
use `docker compose config` without `--quiet` during troubleshooting.

## Backups

`deploy/backup.sh` creates a custom-format PostgreSQL dump and a media tarball in
`/var/backups/tihbc`, logs to `/var/backups/tihbc/backup.log`, writes files with owner-only permissions,
and removes backup artifacts older than seven days. Test one manual run before installing cron:

```bash
chmod 750 deploy/backup.sh
sudo install -d -m 700 -o "$(id -un)" -g "$(id -gn)" /var/backups/tihbc
./deploy/backup.sh
tail -n 20 /var/backups/tihbc/backup.log
```

Install this daily 02:15 UTC cron entry for the deployment user:

```cron
15 2 * * * /usr/bin/flock -n /var/backups/tihbc/backup.lock /opt/tihbc-donor-recall/deploy/backup.sh
```

Copy backups off the VPS according to the server backup policy. A local seven-day copy is not sufficient
protection against VPS loss.

## Restore

Confirm the exact dump and media archive before stopping application services. The restore commands below
replace current database objects and media, so take a fresh backup first.

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml stop tihbc-web tihbc-worker tihbc-api
docker compose --env-file .env.production -f docker-compose.prod.yml exec -T tihbc-db sh -c \
  'pg_restore --clean --if-exists --no-owner --no-privileges --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
  < /var/backups/tihbc/tihbc-db-YYYYMMDDTHHMMSSZ.dump
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm --no-deps --entrypoint sh tihbc-api -c \
  'find /data/media -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + && tar -xzf - -C /data/media' \
  < /var/backups/tihbc/tihbc-media-YYYYMMDDTHHMMSSZ.tar.gz
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
```

## Health checks

Check container health and both public health endpoints:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
curl --fail --show-error --silent https://tihbc.kanwalkumar.com/health/live
curl --fail --show-error --silent https://tihbc.kanwalkumar.com/health/ready
curl --fail --show-error --silent --output /dev/null https://tihbc.kanwalkumar.com/login
```

`/health/live` proves that the API process is running. `/health/ready` additionally checks PostgreSQL and
Redis. A failed public check should be investigated through Caddy and application logs; do not expose a
container port as a workaround.
