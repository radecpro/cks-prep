# 01: Harden the status service

Time budget: 15 minutes
Context: `kind-cks`
Namespace: `cks-lab-01`

## Scenario

The `status` Deployment serves an internal status page. It works, but its container permissions do not meet the workload security requirements. Harden the Deployment and leave the service working.

## Requirements

1. Keep one available replica of Deployment `status`, with its existing container `web`.
2. The application must run with UID **10000** and primary GID **10000**. Explicitly require non-root execution.
3. The container must not be privileged or permit privilege escalation.
4. Drop all Linux capabilities and add none.
5. The container root filesystem must be read-only.
6. Service `status` must still return exactly `cks-lab-01-ready` over HTTP on port **8080**.
7. Persist your changes in the Deployment template; the running Pod must satisfy the same requirements.

Keep the existing image, command, arguments, ConfigMap content, Service selector/port, probes and replica count. Do not add containers, host access, or change resources outside this namespace. A brief rollout interruption is acceptable; wait for completion before grading.

## Start

The initial environment may already be prepared. Inspect it before running setup.

From this directory, `./setup.sh` creates a fresh exercise and refuses to overwrite an existing namespace. It creates only the lab namespace, a ConfigMap, Deployment and Service. Prerequisites: the repository's ready kind cluster, kubectl and Python 3.

Solve using kubectl and Kubernetes documentation. No AI assistance while your timer is running.

## Verification

Run `./verify.sh`. It inspects the Deployment, running Pod, process identity, capability and privilege state, root mount flags, and HTTP response. It prints pass/fail requirements and returns nonzero until all checks pass. It does not repair resources or write inside the container.

## Cleanup / restart

`./cleanup.sh` deletes only namespace `cks-lab-01`, including your work. Run it followed by `./setup.sh` only when you intend to restart the exercise.
