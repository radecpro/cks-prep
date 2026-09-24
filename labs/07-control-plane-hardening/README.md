# Kubelet endpoint hardening

Read [TASK.md](TASK.md). This is the kubelet portion of the planned control-plane hardening topic; API-server configuration is not assessed here.

## Node changes and rollback

Setup changes only `/var/lib/kubelet/config.yaml` in the existing Docker container `cks-worker2`, enabling anonymous authentication and the unauthenticated read-only port 10255. Webhook authentication and authorization remain enabled. It restarts this worker's kubelet, causing a brief interruption to kubelet operations. The read-only endpoint is reachable inside the Docker/Pod network; no new host port is published. Use only this disposable lab cluster.

Before mutation, setup saves the original file, effective configuration and exact Docker container identity in ignored `.local/lab07-state/`. A single state directory prevents concurrent learner/QA runs. Do not delete it or recreate the node until cleanup finishes. The namespace contains only a health-check Pod, ConfigMap and Service.

`./labs/07-control-plane-hardening/cleanup.sh` restores the original file byte-for-byte, restarts kubelet, verifies the original effective configuration and then removes the owned namespace and local state. It refuses a changed container identity or foreign namespace ownership. Restore happens before API operations so it can recover a broken kubelet configuration. If cleanup cannot finish, it retains recovery files and can be rerun.

Emergency manual recovery, for the original `cks-worker2` only (check its container ID against `owner.json` first):

```bash
docker cp .local/lab07-state/config.yaml cks-worker2:/var/lib/kubelet/config.yaml
docker exec cks-worker2 systemctl restart kubelet
./labs/07-control-plane-hardening/cleanup.sh
```

No certificates, API-server manifests, host macOS settings, other nodes, RBAC or cluster-wide admission configuration are changed.

## Commands

```bash
./labs/07-control-plane-hardening/setup.sh
./labs/07-control-plane-hardening/verify.sh
./labs/07-control-plane-hardening/cleanup.sh
```

Verification reads the file, effective kubelet config through authenticated API proxy, systemd status, nodes and lab workloads. HTTP probes test localhost and cross-node read-only exposure, HTTPS anonymous rejection and application health. No repair occurs. A closed port passes only on connection refusal, not a timeout. This verifies selected kubelet settings, not a full CIS audit. Docker Desktop supplies the Linux VM; this does not test a physical host.

Maintainer QA uses `CKS_LAB_NAMESPACE=cks-lab-07-qa` on the same worker sequentially, with complete restoration before learner setup. Setup refuses an existing namespace or saved lab state. Requires Docker, kubectl and Python 3; no extra Python packages.

Curriculum checked 2026-09-21: [CNCF curriculum](https://github.com/cncf/curriculum/tree/f6c7667265fef850daaf93b4e19e919552c67d8c), revision `f6c7667265fef850daaf93b4e19e919552c67d8c`, CKS v1.34 PDF; original cluster hardening practice. References: [kubelet authentication/authorization](https://kubernetes.io/docs/reference/access-authn-authz/kubelet-authn-authz/) and [kubelet configuration](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-config-file/).
