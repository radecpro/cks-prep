# 08: Assess and remediate selected CIS findings

Status: available
Time budget: 20 minutes
Context: kind-cks
Namespace: cks-lab-08
Target node/container: cks-worker2
Prerequisites: Docker, kubectl, Python 3; read README.md for node changes and rollback.

## Scenario

A worker configuration file has insecure filesystem metadata. Assess the two findings with the supplied targeted scanner, remediate them on the actual node, and verify that Kubernetes remains healthy.

## Requirements

1. Run `./labs/08-cis-benchmarks/scan.sh` and inspect the reported file, evidence and control IDs. It evaluates selected `cis-1.12` controls from the pinned kube-bench definitions; it is not the kube-bench executable or a full benchmark run.
2. Remediate findings 4.1.9 and 4.1.10 for the active kubelet configuration file on `cks-worker2`: permissions must allow no bits beyond `0600`, and ownership must be numeric UID/GID 0:0.
3. Preserve the file's exact contents, location and regular-file type. Change only its mode and ownership. Do not substitute a different file, edit the scanner, modify runtime flags, restart/reconfigure the cluster, or change other node files.
4. Preserve the saved recovery state, namespace ownership and `health` Pod in `cks-lab-08`. Kubelet must remain active, all three nodes Ready, API access functional and container exec working on the target node.
5. Rerun the scanner and verifier. Both selected controls must pass. Interpret this result only as those two controls passing, not complete CIS compliance or version-wide benchmark validation.

## Start

If not already prepared, run `./labs/08-cis-benchmarks/setup.sh` from the repository root. It refuses existing lab state or namespace.

## Verification

Run `./labs/08-cis-benchmarks/verify.sh`. It checks live filesystem metadata and content integrity, verifies the kubelet really uses that file, and checks node/workload health without repairing anything. It returns nonzero on failure. The two-control scanner also returns nonzero for failed findings.

## Cleanup

Run `./labs/08-cis-benchmarks/cleanup.sh` to restore the exact original mode and ownership and remove the owned namespace. Keep `.local/lab08-state/` until cleanup succeeds. See README.md for recovery limits.
