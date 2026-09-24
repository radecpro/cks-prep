# Selected CIS filesystem checks

Read [TASK.md](TASK.md) for the 20-minute exercise. `scan.sh` is a small, original two-control auditor based on the upstream tests; it is not kube-bench and does not run the full CIS benchmark.

## Node changes and rollback

Setup targets only `/var/lib/kubelet/config.yaml` in Docker container `cks-worker2`. It records the original mode, UID/GID, content hash, file contents and exact container identity under ignored `.local/lab08-state/`, then sets insecure mode 0666 and ownership 10000:10000. File contents and kubelet settings remain unchanged. No restart is required. A namespaced sleep Pod pinned to that worker provides an exec health check. Do not use this setup outside the disposable kind cluster.

Cleanup restores the saved numeric owner and mode and verifies the original content hash before deleting the owned namespace and recovery state. It refuses a different container identity or changed file contents instead of overwriting unexpected edits. In that case the original file remains in `.local/lab08-state/config.yaml` for deliberate recovery; inspect the change before restoring it. Do not delete recovery state or recreate the node while this lab is active. Restore owner before mode because changing ownership can clear special mode bits.

Original metadata is in `.local/lab08-state/owner.json`. If normal cleanup fails, use those recorded values on the original container's config file, then rerun cleanup. Do not guess the original permissions: cleanup restores the pre-lab state, which is not necessarily CIS-compliant. No certificate files, RBAC, other nodes or host macOS settings are changed.

## Usage and scope

```bash
./labs/08-cis-benchmarks/setup.sh
./labs/08-cis-benchmarks/scan.sh
./labs/08-cis-benchmarks/verify.sh
./labs/08-cis-benchmarks/cleanup.sh
```

Scanner output includes observed mode and numeric ownership. Permission evaluation uses an octal bitmask, not numeric ordering. Grading also checks content integrity, active kubelet config path, service state, API, nodes and the health Pod. It uses read-only inspection and exec. Maintainer QA runs sequentially with `CKS_LAB_NAMESPACE=cks-lab-08-qa` and restores original metadata before learner setup.

Control mapping: 4.1.9 checks the kubelet configuration's mode against 0600; 4.1.10 checks root ownership. Source: [kube-bench cis-1.12/node.yaml](https://github.com/aquasecurity/kube-bench/blob/975ae0039595e2558f7cdbc19cc2a7502acacbfb/cfg/cis-1.12/node.yaml), commit `975ae0039595e2558f7cdbc19cc2a7502acacbfb`, checked 2026-09-24. These selected filesystem tests are applicable to the identified file; the lab does not assert that cis-1.12 is a complete mapping for Kubernetes v1.37 or that kind represents all production CIS controls. Benchmark versions differ, so preserve the pinned control context when interpreting findings.

Curriculum checked 2026-09-24: [CNCF curriculum](https://github.com/cncf/curriculum/tree/f6c7667265fef850daaf93b4e19e919552c67d8c), revision `f6c7667265fef850daaf93b4e19e919552c67d8c`, CKS v1.34 PDF. Original practice for benchmark assessment and node hardening.
