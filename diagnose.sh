#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
echo '=== HOST ==='
docker version --format '{{.Server.Version}}' 2>&1 || true
docker compose version 2>&1 || true
df -h . | tail -1
free -h 2>/dev/null | head -2 || true
echo '=== STACK ==='
docker compose ps 2>&1 || true
echo '=== DASHBOARD HEALTH ==='
curl -s --max-time 8 http://127.0.0.1:8180/healthz 2>&1 || true
echo
echo '=== K3S NODE AND PODS ==='
docker compose exec -T k3s kubectl get nodes 2>&1 || true
docker compose exec -T k3s kubectl get pods -n kics-lab -o wide 2>&1 || true
echo '=== LAST 30 LINES K3S ==='
docker compose logs --tail=30 k3s 2>&1 || true
echo '=== LAST 30 LINES APP ==='
docker compose logs --tail=30 dashboard 2>&1 || true
echo 'Done. Remove any sensitive data before sharing logs.'
