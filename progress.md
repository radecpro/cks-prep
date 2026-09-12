# CKS progress

## Environment

- Repository scaffolded: 2026-09-07.
- Workstation: macOS arm64; kind v0.33.0; Docker server 29.7.2 verified.
- Cluster: `cks` created and verified 2026-09-07; one control plane and two workers, all Ready.
- Kubernetes: v1.37.0; node image: `kindest/node:v1.37.0@sha256:a1ed56cfb0e7b93589bdf97c8cd566405a265939e3620fc4f5de89adff580ae5`.
- Calico: v3.32.2 installed; node DaemonSet and controllers ready.
- Infrastructure checks passed: API readiness, three Ready nodes, CoreDNS, DNS lookup, cross-worker Service HTTP, ingress deny and explicit allow.
- Evidence: `.local/cluster-verification.log`; rerun `./scripts/cluster-verify.sh`. This is infrastructure validation, not a learner assessment.
- Exam date / target version: not recorded; verify official sources.

## Lab status

| Lab | Status | Last attempt | Minutes | Hints | Result / evidence | Retry |
| --- | --- | --- | --- | --- | --- | --- |
| 01-security-context | Passed | 2026-09-11 | Not recorded | Not recorded | verify.sh: 28 checks passed, exit 0 | — |
| 02-rbac | Passed | 2026-09-12 | Not recorded | Not recorded | verify.sh: 42 checks passed, exit 0 | — |
| 03-network-policy | Planned | — | — | — | Not assessed | — |
| 04-pod-security | Planned | — | — | — | Not assessed | — |
| 05-secrets | Planned | — | — | — | Not assessed | — |
| 06-seccomp | Planned | — | — | — | Not assessed | — |
| 07-control-plane-hardening | Planned | — | — | — | Not assessed | — |
| 08-cis-benchmarks | Planned | — | — | — | Not assessed | — |
| 09-supply-chain | Planned | — | — | — | Not assessed | — |
| 10-audit-logging | Planned | — | — | — | Not assessed | — |
| 11-runtime-security | Planned | — | — | — | Not assessed | — |
| 12-system-hardening | Planned | — | — | — | Not assessed | — |

## Weak areas

Lab 01: no failed requirements observed in verification on 2026-09-11. Lab 02: no failed requirements observed in verification on 2026-09-12. Timing and hint usage were not recorded; remaining domains are unassessed.

## Attempt log

Use `templates/REVIEW.md` after each attempt; record failed requirements and evidence here.

### 2026-09-11 — Lab 01 verification

- Command: `./labs/01-security-context/verify.sh`
- Result: PASS; 28 checks passed, zero failures, exit code 0.
- Evidence: Deployment and Pod security settings passed; runtime UID/GID, privilege escalation protection, capability sets and read-only root mount passed. One available replica, completed rollout, expected Service HTTP response and preserved application configuration passed.
- Cluster resources were not modified during grading.
- Elapsed attempt time and hints: not recorded. No failed requirements to remediate from this run.

### 2026-09-11 — Lab transition

- Lab 01 passing attempt and exercise files committed and pushed as `4aae695`.
- Completed Lab 01 namespace removed; exercise source retained for retries.
- Lab 02 authored and maintainer-tested in a separate QA namespace. Initial state fails, passing state passes all 42 checks, excess Secret access and token exposure regressions are detected.
- Learner Lab 02 prepared in its initial unsolved state. No learner assessment yet.

### 2026-09-12 — Lab 02 verification

- Command: `./labs/02-rbac/verify.sh`
- Result: PASS; all 42 checks passed, zero failures, exit code 0.
- Evidence: exact Role permissions and binding subjects; positive and negative authorization checks; default ServiceAccount access removed; Deployment and Pod identity; disabled token automount and absent runtime token; completed rollout and unchanged sample data.
- Cluster resources were not modified during grading.
- Attempt duration and hints: not recorded. No failed requirements identified by this verifier.
