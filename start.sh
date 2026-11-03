#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"

if command -v pveversion >/dev/null 2>&1 || [ -d /etc/pve ]; then
  echo 'ERROR: Do not run this classroom lab on the Proxmox hypervisor.' >&2
  echo 'Deploy it on a dedicated Ubuntu VM/ECS with Docker Engine.' >&2
  exit 1
fi
if ! command -v docker >/dev/null 2>&1; then
  echo 'ERROR: Docker Engine not detected. Install Docker Engine + Compose plugin first.' >&2
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo 'ERROR: Docker Compose v2 plugin is missing.' >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo 'ERROR: This account cannot access Docker. Check group membership / sudo.' >&2
  exit 1
fi
if [ ! -f .env ]; then
  if command -v openssl >/dev/null 2>&1; then
    SECRET=$(openssl rand -hex 25)
  elif command -v python3 >/dev/null 2>&1; then
    SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(25))')
  else
    echo 'ERROR: Need openssl or Python 3 to generate the initial Grafana password.' >&2
    exit 1
  fi
  umask 077
  {
    echo '# Use LAB_BIND_IP=0.0.0.0 ONLY with restricted firewall/security group and a trusted network.'
    echo 'LAB_BIND_IP=127.0.0.1'
    printf 'GRAFANA_ADMIN_PASSWORD=%s\n' "$SECRET"
  } > .env
  chmod 600 .env
  echo 'Generated .env with a random Grafana password (file permissions 600).'
else
  echo 'Keeping existing .env and Grafana credentials.'
fi

# Never delete/recreate a student's cluster on a subsequent launch.
echo 'Checking Compose configuration...'
docker compose config --quiet
printf '\nStarting dedicated KICS Kubernetes training stack...\n'
docker compose up -d --build
printf '\nDocker services:\n'
docker compose ps
cat <<'OUT'

KICS LAB:
  Teaching UI:  http://127.0.0.1:8180
  Kubernetes demo: http://127.0.0.1:8188
  Grafana:      http://127.0.0.1:8300 (admin, password in protected .env)
  Prometheus:   http://127.0.0.1:8909
  Portainer CE: https://127.0.0.1:9444 (initial setup required)

First startup downloads K3s, app images and monitoring images. Wait for
'Kubernetes connected' in the web UI; do not start clicking while it is initializing.

From a remote laptop, use SSH port forwarding (see docs/STUDENT_GUIDE.md).
To use kubectl without installing it on the host:
  ./kubectl.sh get pods -n kics-lab -o wide

Safe inspection commands:
  docker compose ps
  docker compose logs --tail=80 k3s dashboard
  ./diagnose.sh
OUT
