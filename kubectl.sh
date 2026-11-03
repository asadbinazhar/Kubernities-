#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"
if [ "$#" -eq 0 ]; then
  echo 'Usage: ./kubectl.sh get pods -n kics-lab -o wide'
  exit 1
fi
# Kubernetes CLI is shipped inside the k3s Docker image; nothing to install on ECS.
docker compose exec -T k3s kubectl "$@"
