# Student practical — Kubernetes Blue-Green, Canary and Observability

## Open your lab

The instructor will provide a **dedicated Ubuntu ECS/VM** containing Docker Engine and Docker Compose v2. Unzip the lab and run the **only startup command** from the extracted directory:

```bash
./start.sh
```

You do **not** type any program code into the browser application and you do not need a classroom access PIN. Open the teaching UI through your SSH tunnel at `http://localhost:8180`.

### First startup checklist

- Wait for dashboard badge **Kubernetes connected** (first launch must download images).
- Verify Blue, Green and Router Deployments appear and have Ready replicas.
- Open live demo `http://localhost:8188` (through SSH forward). At first, Blue v1 should answer.
- If it fails, use `./diagnose.sh` and report its last error line to instructor. Never delete volumes as a troubleshooting step.

## 8 classroom checkpoints

1. **Pod readiness:** show `kics-blue`, `kics-green` and two `kics-router` Ready Pods.
2. **Blue-Green:** click **Switch 100% to Green**, wait for router Ready and refresh demo; it should show GREEN v2.
3. **Rollback:** click **Send 100% to Blue**, wait and refresh; it should show BLUE v1.
4. **Canary:** select 25% Green; wait for router Ready; click **Send 24 Test Requests**. Results should show a mixture *on average*, not necessarily exactly 6/18.
5. **Rolling:** select **Roll Blue to v2**, inspect `ReplicaSets`, confirm a new ReplicaSet was created, then **Restore Blue v1**.
6. **Scaling:** scale Blue to 3, inspect desired/ready Pods, then scale to 1. Disable HPA first if HPA was enabled.
7. **Observability:** check Prometheus counters and a Grafana graph after generating traffic. These metrics report lab operations and sampled traffic, not complete physical node metrics.
8. **Troubleshooting:** open `Events`, `Blue Logs` and `Describe Router`, explain how a readiness failure differs from a crash-loop.

## Kubectl on the ECS (optional)

The K3s container **already includes kubectl**; you do not install it again on the ECS.

```bash
./kubectl.sh get pods -n kics-lab -o wide
./kubectl.sh get deployments,replicasets,services -n kics-lab
./kubectl.sh rollout status deployment/kics-blue -n kics-lab
./kubectl.sh describe pod -n kics-lab <POD_NAME>
./kubectl.sh get events -n kics-lab --sort-by=.lastTimestamp
```

The commands above are optional: the GUI lets you inspect the same data without typing commands. Do not paste `<POD_NAME>` literally; use a real Pod name when executing that example.

## End of session evidence

Submit a screenshot showing: the selected canary percentage, mixed sample outcomes, healthy Deployments, plus a Grafana graph. Write one paragraph describing which update strategy was safest for a critical application and why.
