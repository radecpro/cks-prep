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
| 03-network-policy | Passed | 2026-09-14 | Not recorded | DNS diagnosis on first attempt | Retry: 49 passed, 0 failed; exit 0 | — |
| 04-pod-security | Passed | 2026-09-14 | Not recorded | None provided during grading | 16 passed, 0 failed; exit 0 | — |
| 05-secrets | Passed | 2026-09-20 | Not recorded | None during grading | 32 passed, 0 failed; exit 0 | — |
| 06-seccomp | Planned | — | — | — | Not assessed | — |
| 07-control-plane-hardening | Planned | — | — | — | Not assessed | — |
| 08-cis-benchmarks | Planned | — | — | — | Not assessed | — |
| 09-supply-chain | Planned | — | — | — | Not assessed | — |
| 10-audit-logging | Planned | — | — | — | Not assessed | — |
| 11-runtime-security | Planned | — | — | — | Not assessed | — |
| 12-system-hardening | Planned | — | — | — | Not assessed | — |

## Weak areas

Lab 01: no failed requirements observed in verification on 2026-09-11. Lab 02: no failed requirements observed in verification on 2026-09-12. Lab 03: namespace label selection caused DNS failures on the first attempt; corrected by the learner and passing on retry, 2026-09-14. Revisit namespace selectors in later mixed practice. Lab 04: no failed requirements observed on 2026-09-14. Timing was not recorded; remaining domains are unassessed.

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

### 2026-09-12 — Lab 03 preparation (maintainer QA)

- Created NetworkPolicy exercise with four Pods, one Service, default-deny requirements and a traffic matrix.
- Disposable `cks-lab-03-qa`: unrestricted baseline failed 25 checks; passing configuration passed all 49 checks; opening TCP 9090 triggered the expected single failure. Duplicate setup correctly refused the existing namespace.
- Evidence: `.local/lab03-initial.log`, `.local/lab03-passing.log`, `.local/lab03-regression.log`, `.local/lab03-duplicate-setup.log`.
- Shell syntax and Python parsing passed. QA resources and temporary passing configuration removed; learner namespace prepared without policies.
- Verification limitations: bounded traffic matrix; review extra policy grants, namespace/DNS scope and both directions independently. TCP DNS checks connection establishment only. No full external-egress test.
- Learner attempt, elapsed time, hints and weak areas: not assessed. Maintainer QA is not a passing learner attempt.

### 2026-09-14 — Lab 03 verification

- Command: `./labs/03-network-policy/verify.sh`; exit 1, 40 checks passed and 9 failed.
- Evidence: `.local/lab03-attempt-2026-09-14.log`.
- Failed requirements: UDP DNS resolution and TCP DNS connectivity from all four Pods (8 checks), plus frontend access to the API Service by DNS name (1 check).
- Passed: fixture integrity and readiness, local listeners, default denial in both directions, direct frontend-to-API TCP 8080 and every forbidden Pod/port connection in the matrix.
- Additional read-only test: frontend HTTP to API Service ClusterIP returned `cks-lab-03-ready`; Service networking works without DNS.
- Diagnosis: applied `allow-dns` selects namespace label `name=kube-system`, absent on the actual namespace, which has `kubernetes.io/metadata.name=kube-system`. CoreDNS Pods match the Pod selector and have ready endpoints. The combined peer therefore selects no DNS destinations.
- Weak area: distinguish namespace names from namespace labels when using NetworkPolicy selectors.
- Elapsed attempt time: not recorded. Assistance: targeted DNS diagnosis supplied after the learner reported the problem. No policies, workloads or learner manifests changed during review.
- Retry: after learner correction. Bounded verifier limitations remain as documented in the lab README.

### 2026-09-14 — Lab 03 retry verification

- Command: `./labs/03-network-policy/verify.sh`; exit 0, all 49 checks passed, zero failures.
- Evidence: `.local/lab03-attempt-2026-09-14-retry.log`.
- DNS UDP resolution and TCP connectivity passed for all four Pods; frontend access via API DNS name and direct Pod IP passed. Every denied Pod/port pair remained blocked; fixture integrity and readiness passed.
- Read-only policy review confirmed the corrected namespace label selector and combined CoreDNS Pod selector, UDP/TCP 53 only, namespace-wide default deny in both directions, and the scoped frontend-to-API TCP 8080 exceptions without additional grants in these four policies.
- Learner corrected the policy after the prior DNS diagnosis. No additional hints this retry; attempt duration not recorded. No solution files or cluster resources modified during grading.
- No failed requirements remain in this assessment. TCP DNS validation checks connection establishment; traffic testing remains bounded as documented in the README.

### 2026-09-14 — Lab 03 cleanup and Lab 04 preparation

- Lab 03 source, learner manifests and passing retry committed and pushed as `ca5d188`; remote main verified at the same commit.
- Removed owned `cks-lab-03` namespace after publication.
- Authored Lab 04 Pod Security Admission exercise. QA baseline: 10 passed, 6 failed. Compliant configuration: all 16 passed. Weakening enforcement to Baseline: 14 passed, 2 failed, including the privilege escalation admission probe.
- Corrected the privileged negative probe during QA to avoid contradictory settings rejected by API validation before Pod Security Admission. Waiting for old rollout Pods to terminate is required for the final single-Pod check.
- Evidence: `.local/lab04-initial.log`, `.local/lab04-passing.log`, `.local/lab04-regression.log`, `.local/lab04-duplicate-setup.log`.
- Duplicate setup refused the existing namespace. Changed shell scripts passed syntax checks, Python parsing passed, and git diff whitespace checks passed.
- Removed QA namespace and temporary passing patch; prepared learner namespace `cks-lab-04` in the original insecure state with an available status Deployment.
- No learner attempt, duration or hints recorded for Lab 04. Admission tests use non-persistent server-side dry runs; audit-log delivery is not tested. Maintainer QA is not a learner assessment.

### 2026-09-14 — Lab 04 verification

- Command: `./labs/04-pod-security/verify.sh`; exit 0, all 16 checks passed, zero failures.
- Evidence: `.local/lab04-attempt.log`.
- Requirements passed: Restricted enforce/warn/audit labels pinned to v1.37; ownership label retained; preserved application fixtures; completed rollout with one Ready available replica; runtime web process UID/GID 10000; original Service HTTP response.
- Admission evidence: fresh template and running Pod specifications accepted in server-side dry runs; privileged and privilege-escalation probes rejected by Pod Security Admission. No probe Pods persisted.
- Failed requirements / observed weak areas: none in this assessment. Attempt duration and outside hint usage not recorded; no hints provided during grading.
- Verification limits: audit configuration labels checked, audit-log delivery not tested; no exhaustive audit of cluster-wide admission configuration changes.
- Learner manifests and cluster resources were not modified. No cleanup performed.

### 2026-09-17 — Lab 04 cleanup and Lab 05 preparation

- Lab 04 source and passing assessment committed and pushed as `193a47e`; remote main verified at the same commit. Bundled Git and GitHub CLI authentication used because Apple Git requires Xcode license acceptance; no system settings changed.
- Removed owned `cks-lab-04` namespace after publication.
- Authored Lab 05 Secret exposure exercise with synthetic credentials, two containers, scoped projection and runtime file/environment checks.
- QA baseline: 21 passed, 11 failed. Passing configuration: all 32 passed. Reintroducing a sidecar credential mount and broad file permissions: 26 passed, 6 failed. Duplicate setup refused the existing namespace.
- Evidence: `.local/lab05-initial.log`, `.local/lab05-passing.log`, `.local/lab05-regression.log`, `.local/lab05-duplicate-setup.log`.
- Shell syntax, Python parsing and Git whitespace checks passed. QA namespace and temporary passing patch removed. Learner namespace `cks-lab-05` prepared in its original insecure state with a Ready two-container Pod.
- Learner attempt, timing, hints and weak areas: not assessed. Current process environments and logs are tested; historical logs, external stores, rotation and etcd encryption at rest are not assessed.

### 2026-09-20 — Lab 05 verification

- Command: `./labs/05-secrets/verify.sh`; exit 0, all 32 checks passed.
- Evidence: `.local/lab05-attempt-2026-09-20.log`.
- Passed: original Secret and application fixtures; template and running Pod projection restricted to password; read-only mounts and runtime mode 0440; no sidecar mounts or credential files; no environment injection or credential values in current process environments/logs; completed rollout and healthy Service response.
- Failed requirements / observed weak areas: none. Attempt duration and outside hints not recorded; no hints provided during grading.
- No cluster resources or learner solution files changed during assessment. Historical/external logs and encryption at rest remain outside this lab's checks.
