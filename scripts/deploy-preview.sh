#!/usr/bin/env bash
# Build both tracks and publish them to the preview host.
#
# The preview runs on sra-oracle behind the Cloudflare Tunnel that already
# serves shiny and koito there, so it stays up regardless of whether this
# laptop is on. That is the whole point: the project lead needs a link, not a
# VPN invite and a machine that has to stay awake.
#
#   scripts/deploy-preview.sh          build, then sync both tracks
#   scripts/deploy-preview.sh --setup  also push the compose stack and start it
#
# Dashboard routing (one-time, and not scriptable because the tunnel is
# token-managed) is documented in docs/preview-hosting.md.

set -euo pipefail

HOST="${PREVIEW_HOST:-sra-oracle}"
REMOTE="${PREVIEW_DIR:-/home/ubuntu/eos-preview}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }

say "Building all three"
make build
make build-wiki

if [[ "${1:-}" == "--setup" ]]; then
  say "Provisioning the preview stack on $HOST"
  ssh "$HOST" "mkdir -p $REMOTE/zola $REMOTE/astro $REMOTE/wiki $REMOTE/conf $REMOTE/conf-wiki"
  rsync -az deploy/docker-compose.yml "$HOST:$REMOTE/"
  rsync -az deploy/nginx-preview.conf "$HOST:$REMOTE/conf/default.conf"
  rsync -az deploy/nginx-wiki.conf "$HOST:$REMOTE/conf-wiki/default.conf"
  # compose v2 ships as a docker plugin here
  ssh "$HOST" "cd $REMOTE && sudo docker compose up -d"
fi

say "Syncing content"
rsync -az --delete zola/public/  "$HOST:$REMOTE/zola/"
rsync -az --delete astro/dist/   "$HOST:$REMOTE/astro/"
rsync -az --delete wiki/dist/    "$HOST:$REMOTE/wiki/"

say "Syncing nginx config"
rsync -az deploy/nginx-preview.conf "$HOST:$REMOTE/conf/default.conf"
rsync -az deploy/nginx-wiki.conf "$HOST:$REMOTE/conf-wiki/default.conf"

say "Reloading nginx"
# Config is bind-mounted, so a reload picks up header changes without downtime.
ssh "$HOST" "for c in eos-zola eos-astro eos-wiki; do \
               sudo docker exec \$c nginx -s reload 2>/dev/null || true; done"

say "Checking the origin responds"
ssh "$HOST" '
for p in 8081 8082 8083; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$p/" || echo ---)
  printf "  localhost:%s  ->  %s\n" "$p" "$code"
done'

cat <<'DONE'

Deployed. Public URLs, once the tunnel hostnames exist:

  https://eos-zola.sradjoker.cc
  https://eos-astro.sradjoker.cc
  https://eos-wiki.sradjoker.cc

If those 404 or hang, the dashboard routing is not set up yet.
See docs/preview-hosting.md.
DONE
