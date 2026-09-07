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
| 01-security-context | Planned | — | — | — | Not assessed | — |
| 02-rbac | Planned | — | — | — | Not assessed | — |
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

Not assessed. Do not infer strengths from work experience alone.

## Attempt log

Use `templates/REVIEW.md` after each attempt; record failed requirements and evidence here.
