# KICS Kubernetes Deployment Studio — v2 (Real K3s)

**Classroom focus:** Kubernetes / kubectl, blue-green, canary, rolling revisions, deployment restart, replica scaling, HPA, ConfigMaps, Secrets (metadata only), readiness and liveness probes, namespaces, Services, pod logs, events, ReplicaSets, metrics, Grafana and Portainer.

## Important distinction from the previous package

This is a **rebuilt, self-contained replacement**, not a patch against the exact earlier lab: the prior ZIP/startup error output was not available to inspect. It is designed to remove copy-paste `cat <<EOF` code blocks, separate application and cluster startup, and use a single entry-point script. It **has not been end-to-end run on a Docker host in the authoring environment**; test it on one disposable VM before handing it to the whole class.

## Requirements

- Dedicated **Ubuntu 22.04 / 24.04 ECS or VM**, Linux x86_64, Docker Engine and **Docker Compose v2** pre-installed.
- Recommended **4 vCPU, 8 GiB RAM, 35 GiB free disk**; downloads require working outbound HTTPS/DNS. Nested K3s requires a privileged container and working cgroups/overlay support. Some restricted Huawei KooLabs ECS environments may **not permit** running nested Kubernetes.
- **Do not** install on the Proxmox hypervisor or a multi-tenant production Docker host.
- Training stack is deliberately localhost-bound; instructor uses SSH port forwarding. **No PIN/password/code in the teaching UI**. That makes it unsuitable for exposure directly to the public internet.

## Install — one launch command

1. Upload and unzip this ZIP on the student's dedicated Ubuntu ECS/VM.
2. Inside its folder run:

```bash
./start.sh
```

First startup can take several minutes to pull images. Do not launch a second copy. To inspect:

```bash
./diagnose.sh
```

## Open the UI, with no PIN or code

From the Ubuntu host browser: `http://127.0.0.1:8180`

From a Windows PC, run the following on **Windows PowerShell** and then open URLs on the **Windows** browser:

```powershell
ssh -L 8180:127.0.0.1:8180 -L 8188:127.0.0.1:8188 -L 8300:127.0.0.1:8300 -L 8909:127.0.0.1:8909 -L 9444:127.0.0.1:9444 ubuntu@YOUR_ECS_EIP
```

- Teaching dashboard: http://localhost:8180
- Live K3s demo website: http://localhost:8188
- Grafana: http://localhost:8300 (initial admin password in `.env`, never share it)
- Prometheus: http://localhost:8909
- Portainer CE: https://localhost:9444 (self-signed TLS certificate; create its **own** admin on first visit)

For a class on an isolated private LAN, you may set `LAB_BIND_IP=0.0.0.0` in `.env`, then `docker compose up -d`, **only after restricting the ECS security group/firewall to trusted instructor/student IPs**. This also exposes the demo on port 8188. Grafana, Prometheus, Portainer remain bound to localhost and need SSH tunneling. **Never expose port 6443, Docker socket or the privileged K3s API to the public internet.**

## What students do in the browser

1. Blue–Green switch: blue v1 -> green v2 -> rollback to blue.
2. Canary traffic: choose Green weights of 10%, 25%, 50%, 75%, 100%; run 24-request sample and observe *approximate* distribution.
3. Rolling update: Blue v1 -> v2 -> v1 via pod-template/immutable ConfigMap change; observe ReplicaSets.
4. Replicas/HPA: manually scale 1/2/3 or enable HPA (CPU metrics-server; actual scaling requires CPU load).
5. Kubectl Explorer: nodes, namespaces, pods, deployments, ReplicaSets, Services, ConfigMaps, Secret names (no values), events, HPA, top, workload logs/description.
6. Grafana: preloaded panels for traffic, operations, pod readiness and cluster availability.
7. Portainer: view host Docker stack. Portainer **does not automatically control the nested K3s**.

## Real Kubernetes rather than UI simulation

Docker Compose runs one **privileged K3s server container**. `dashboard` uses the generated Kubeconfig and the official Kubernetes Python client to create real Pods, Deployments, ReplicaSets, Services, ConfigMaps, a dummy Secret, and a NodePort. `nginx` running **inside K3s** performs weighted upstream routing between Blue/Green services; a rollout restarts router Pods so Nginx reloads the updated ConfigMap. Observed percentages are probabilistic; 24 requests never guarantee an exact ratio. Neither K8s nor Compose performs true weighted HTTP routing by itself.

**Load demonstration warning:** HPA exists but is not guaranteed to scale without sufficient CPU pressure and a healthy Metrics Server.

## More kubectl practice (no Kubernetes install needed on host)

```bash
./kubectl.sh get nodes -o wide
./kubectl.sh get pods -n kics-lab -o wide
./kubectl.sh get deploy,rs,svc -n kics-lab
./kubectl.sh describe deploy kics-blue -n kics-lab
./kubectl.sh rollout status deployment/kics-blue -n kics-lab
./kubectl.sh rollout history deployment/kics-blue -n kics-lab
./kubectl.sh logs deployment/kics-blue -n kics-lab --tail=30
./kubectl.sh get events -n kics-lab --sort-by=.lastTimestamp
./kubectl.sh top pods -n kics-lab
./kubectl.sh get hpa -n kics-lab
```

`./kubectl.sh` **executes inside the K3s server container**. CLI commands can access the cluster and are intended for the instructor; do not paste malicious commands from untrusted sources. Do not delete the `kics-lab` namespace until the classroom exercise ends.

## Existing resource protection

All Docker volumes are named within project `kics-kubernetes-lab`. The script never invokes `docker system prune`, volume deletion or Docker network cleanup. This is nevertheless **not a zero-risk production deployment**: nested K3s requires `privileged: true` and Portainer has read/write host Docker socket access. Use a disposable ECS.

## Day-to-day controls

```bash
# check status
docker compose ps
# app diagnostics
./diagnose.sh
# stop WITHOUT deleting volumes
docker compose stop
# resume
docker compose up -d
# never use 'down -v' unless you intentionally want to erase the whole lab
```

### Troubleshooting

| Symptom | Investigation |
|---|---|
| UI starts but says initializing | `docker compose logs -f k3s dashboard`; wait for kubeconfig and cluster readiness. |
| `./start.sh`: Compose not found | Install Docker Compose **v2 plugin**, verify `docker compose version`. |
| UI shows Kubernetes TLS certificate error | Verify `--tls-san=k3s` in compose, Kubeconfig volume is correct, and no old incompatible cluster state is being reused. |
| Pods `ImagePullBackOff` | Verify Ubuntu ECS DNS, outbound HTTPS, Docker registries and free space. |
| Port 8180/8188 already used | Inspect with `ss -lntp`; stop only the conflicting **lab** service or adjust mapping. |
| Portainer cannot log in | Set up separate Portainer admin within its first-run setup window; restart only `portainer` if setup times out. |
| Dashboard works but demo is 502 | Check `./kubectl.sh get pods,svc,endpoints -n kics-lab`, logs and readiness; allow images to pull. |
| Grafana shows no samples | Run the 24-request sample from dashboard, wait 1–2 scrape cycles and set Grafana to Last 30 minutes. |
| HPA not scaling | Metrics Server available? `./kubectl.sh top pods -n kics-lab`. CPU needs actual load. |
| Access from external browser fails | This deployment intentionally binds to 127.0.0.1. Use SSH tunnel. |

Read `docs/STUDENT_GUIDE.md` for classroom sequence and `docs/INSTRUCTOR_QA.md` for assessment and validation.
