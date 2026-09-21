# 06: Apply runtime seccomp protection

Status: available
Time budget: 15 minutes
Context: kind-cks
Namespace: cks-lab-06
Prerequisites: running repository kind/containerd cluster with seccomp support; kubectl and Python 3.

## Scenario

A status service has a web container and an observer sidecar. Its deployment currently opts out of seccomp protection. Apply the runtime's default profile consistently while preserving the service.

## Requirements

1. Deployment `status` must explicitly set the Pod-level seccomp profile to `RuntimeDefault`.
2. Both containers must effectively use `RuntimeDefault`; no container may override it with `Unconfined` or `Localhost`.
3. Complete the rollout so both running container PID 1 processes report seccomp filter mode (`Seccomp: 2`). Keep UID/GID 10000 and the existing non-privileged security settings.
4. Finish with exactly one Ready Pod and one available replica. Preserve names, images, commands, arguments, labels, volumes, mounts, readiness probe, ConfigMap, Service and disabled service-account token automount. Service `status:8080` must return `cks-lab-06-ready`.
5. Change only Pod/container `seccompProfile` fields in the Deployment. Do not add containers, change namespace admission rules, modify kubelet configuration or install node profiles.

## Start

If not already prepared, run `./labs/06-seccomp/setup.sh` from the repository root. Setup refuses an existing namespace.

## Verification

Run `./labs/06-seccomp/verify.sh`. It reads the Deployment and running Pod, checks both PID 1 processes through `/proc/1/status`, and tests the Service. It returns nonzero on unmet requirements and never repairs the workload.

## Cleanup

Run `./labs/06-seccomp/cleanup.sh` to delete only this owned namespace. No node files or cluster-wide settings are changed.
