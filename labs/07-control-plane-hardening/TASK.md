# 07: Harden a worker kubelet

Status: available
Time budget: 25 minutes
Context: kind-cks
Namespace: cks-lab-07
Target node/container: cks-worker2
Prerequisites: repository kind cluster, Docker, kubectl and Python 3. Read the node-change and rollback section in README.md before starting.

## Scenario

A worker exposes a read-only kubelet endpoint and accepts anonymous identities on its secure endpoint. Harden the node while keeping authenticated management and workloads available.

## Requirements

1. Disable the kubelet read-only listener. TCP 10255 must refuse connections from the node itself and another cluster node.
2. Disable anonymous authentication on the kubelet HTTPS endpoint. Unauthenticated requests to `/pods` on TCP 10250 must receive HTTP 401, while authenticated kubelet API access remains functional.
3. Preserve webhook authentication, Webhook authorization and all other original kubelet settings. Apply changes to `/var/lib/kubelet/config.yaml` on `cks-worker2`; do not substitute firewall rules or command-line overrides.
4. Ensure your settings are both saved on disk and active in the running kubelet. Kubelet must remain active, all three nodes Ready, and the Kubernetes API healthy.
5. Preserve the `health` Pod pinned to `cks-worker2`, its ConfigMap and Service in `cks-lab-07`. HTTP through `health:8080` must return `cks-lab-07-ready`; container exec and logs must remain functional.
6. Change only the two kubelet settings implicated above, and restart that node's kubelet as needed. Do not modify other files/nodes, workload resources, namespace labels, RBAC, API-server settings or the saved recovery files.

## Start

The environment may already be prepared. Otherwise run `./labs/07-control-plane-hardening/setup.sh` from the repository root. It creates a node backup before introducing the insecure configuration and refuses an existing lab state.

## Verification

Run `./labs/07-control-plane-hardening/verify.sh`. It verifies disk configuration, active settings, endpoint behavior and cluster/application health without modifying them. A saved-but-not-loaded change is insufficient.

## Cleanup

Run `./labs/07-control-plane-hardening/cleanup.sh` to restore the original worker configuration and remove the namespace. Recovery instructions are in README.md. Keep the backup until cleanup succeeds.
