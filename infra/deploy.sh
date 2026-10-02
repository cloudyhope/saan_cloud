#!/bin/sh
# Update the Saan App stack on the shared Cloubit VPS. Run on the server as root.
#
#   /opt/apps/saanapp/infra/deploy.sh            # pull, build one service at a time, restart this project only
#   /opt/apps/saanapp/infra/deploy.sh --no-pull  # rebuild the code already on disk
#
# Safety on a shared host:
#   - it only touches /opt/apps/saanapp and the compose project named `saanapp`;
#   - images build one service at a time at low CPU priority, so neighbours keep their memory and CPU;
#   - nothing is stopped before its replacement is built (a failed build leaves the running stack alone).
set -eu

APP_DIR=/opt/apps/saanapp
COMPOSE="docker compose --project-name saanapp --env-file $APP_DIR/.env -f $APP_DIR/infra/docker-compose.prod.yml"

cd "$APP_DIR"
if [ "${1:-}" != "--no-pull" ]; then
    git pull --ff-only
fi

[ -f .env ] || { echo "Missing $APP_DIR/.env (see infra/saanapp.env.example)"; exit 1; }
docker network inspect web >/dev/null 2>&1 || { echo "The shared network 'web' is missing"; exit 1; }

echo "Free memory before building:"; free -m | sed -n '1,2p'
for service in api panel web; do
    echo "== build $service"
    nice -n 19 ionice -c3 $COMPOSE build "$service"
done

echo "== start"
$COMPOSE up -d
$COMPOSE ps
docker image prune -f >/dev/null
echo "Done. Check: curl -sI https://webapi.saanapp.ir/health/ | head -1"
