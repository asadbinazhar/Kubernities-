# Instructor deployment review and risk management

## Scope and constraints

**This package creates real, nested Kubernetes** in a privileged K3s Docker container. Portainer accesses the host Docker socket. It is suitable for one disposable teaching ECS/VM **only**, not a shared Proxmox host or production machine. Do not distribute until one pilot ECS succeeds.

### Pilot validation

1. `docker compose config --quiet` before deployment.
2. `./start.sh`; note that the initial image pull may take minutes depending on internet/DNS.
3. `docker compose ps` and `./diagnose.sh`. Verify the K3s node Ready and no image pull errors.
4. Verify `http://localhost:8180/healthz` is reachable through an SSH tunnel.
5. Verify `http://localhost:8188` initially serves `BLUE RELEASE / Version v1`.
6. In GUI switch 100% Green, wait for router Ready; demo should display Green v2. Switch back Blue.
7. Apply 25% Green; sample at least 100 requests if testing distribution statistically. Small samples vary, not proof of malfunction.
8. Roll Blue to v2, inspect `kubectl get rs -n kics-lab`, then restore v1.
9. Scale from 1 to 2; verify Ready pod count updates. Enable/disable HPA, verify HPA object appears/disappears; actual autoscaling requires CPU load and metric availability.
10. Verify Prometheus target `dashboard:8000` is UP, Grafana dashboard contains time-series metrics after traffic sampling. Open Portainer separately and finish its first-run admin setup.
11. `docker compose stop` then `docker compose up -d`, confirm cluster state/portainer/grafana persist without losing volumes.
12. Validate isolated deployment leaves existing host services untouched. Pilot on disposable VM recommended.

### Explicit student failure modes

| Failure | Safe diagnostic |
|---|---|
| `docker compose: command not found` | Install Compose v2; do NOT use outdated `docker-compose` blindly. |
| Docker permission denied | Check `docker info`; grant group or execute from authorized sudo session. |
| K3s `operation not permitted` | Check privileges/cgroups; use dedicated VM with nesting support; some KooLabs disallow privileged workloads. |
| Kubeconfig not ready | K3s health + service logs; do not regenerate manually or change certificates. |
| DNS timeout pulling images | Verify ECS DNS and security-group egress, image registry access. |
| Kubelet OOM | Use at least 8 GiB RAM; check free memory and disk. |
| Port occupied | Check `ss -lntp`; change LAB_BIND_IP/host mappings with permission; don't kill other services. |
| Grafana panel no data | Open status dashboard, wait Prom scrape, run a request sample. |
| Portainer HTTPS warning | Self-signed initial cert; use SSH tunnel and controlled browser. |

### Security boundaries

- GUI has NO authentication by design. It uses fixed, validated operations only. **Bind 127.0.0.1 and use SSH forwarding** unless in an isolated, access-controlled classroom network.
- `Portainer` can control the host's Docker and is therefore effectively privileged. Never expose it on internet. Its password is not the Grafana password.
- k3s API port 6443 is only on the Compose network; no host port is published.
- The kubeconfig is shared only within a Docker named volume to dashboard (read-only there). Do not copy kubeconfig outside the trusted ECS or print it in student materials.
- Teaching Secret contains an obviously dummy string; UI deliberately redacts values.
- No scripts run `docker prune` or `down -v` or modify pre-existing Docker volumes.

### Suggested assessment criteria

Each practical checkpoint may carry 10 marks: real Ready workloads, Blue/Green switch, rollback, canary observed, rolling ReplicaSet evidence, scaled replicas, event/log explanation, and Grafana metric evidence. Do not mark a student as completed simply because the dashboard opened. Instructors should spot-check operation state via kubectl output.
