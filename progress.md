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
| 06-seccomp | Passed | 2026-09-21 | Not recorded | None during grading | 25 passed, 0 failed; exit 0 | — |
| 07-control-plane-hardening | Passed | 2026-09-21 | Not recorded | None during grading | 17 passed, 0 failed; exit 0 | — |
| 08-cis-benchmarks | Passed | 2026-09-24 | Not recorded | None during grading | Selected controls passed; 10/10 verifier checks | — |
| 09-supply-chain | Passed | 2026-09-24 | Not recorded | None during grading | 21 passed, 0 failed; exit 0 | — |
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

### 2026-09-20 — Lab 05 cleanup and Lab 06 preparation

- Lab 05 exercise and passing assessment committed and pushed as `f5136f5`; remote main verified at that commit. Removed owned `cks-lab-05` namespace after publication.
- Authored Lab 06 RuntimeDefault seccomp exercise with two containers, Pod/container profile checks and PID 1 runtime evidence. No node or cluster-wide configuration changes.
- QA baseline: 17 passed, 8 failed, including filter-mode checks for both processes. Passing state: 25 passed. Sidecar Unconfined regression: 22 passed, 3 failed (template, running Pod, runtime filter mode).
- Evidence: `.local/lab06-initial.log`, `.local/lab06-passing.log`, `.local/lab06-regression.log`, `.local/lab06-duplicate-setup.log`.
- Duplicate setup refused the existing namespace. Shell syntax, Python parsing and Git whitespace checks passed. QA namespace and temporary patch removed; original insecure learner environment prepared in `cks-lab-06`.
- Runtime seccomp mode changes were observed on this kind/containerd environment. Exact syscall allowlists, custom Localhost profiles and host-level default settings are not assessed.
- Learner attempt, timing, hints and weak areas for Lab 06: not assessed. Lab 05 had no failed requirements in the observed assessment.

### 2026-09-21 — Lab 06 verification

- Read-only `./labs/06-seccomp/verify.sh`: all 25 passed, exit 0. Evidence: `.local/lab06-attempt-2026-09-21.log`.
- Both template and live Pod use RuntimeDefault effectively. Both PID 1 processes report filter mode; identity, privilege constraints, original fixtures, rollout and Service response passed.
- No failed requirements observed. Duration and outside hint use not recorded; no hints supplied during grading. Exact syscall allowlists and custom profiles were not assessed.
- No learner manifests or cluster resources changed during verification.

### 2026-09-21 — Lab 06 cleanup and Lab 07 preparation

- Lab 06 exercise, learner manifest and passing assessment committed and pushed as `49dcb1a`; verified remote main. Removed its owned namespace.
- Lab 07 is a kubelet-hardening exercise on `cks-worker2`. Node changes and rollback documented before execution; setup backs up original file/effective configuration and container identity under ignored `.local/lab07-state/`.
- QA: insecure baseline 10 passed / 7 failed; repaired disk without restart 12 / 5; fully loaded repaired state 17 / 0; insecure saved port regression while live settings remained hardened 16 / 1. Shortly after restart exec/logs needed kubelet synchronization before passing.
- Evidence: `.local/lab07-initial.log`, `.local/lab07-not-restarted.log`, `.local/lab07-passing.log`, `.local/lab07-regression.log`, `.local/lab07-duplicate-setup.log`, `.local/lab07-rollback.log`.
- Duplicate setup refused existing recovery state. Cleanup verified original file byte-for-byte, original effective settings and worker readiness, then removed QA namespace and recovery state. Shell syntax, Python parsing and Git whitespace checks passed.
- Learner setup then saved a fresh original backup, enabled the two insecure kubelet settings, and created the Ready health workload in `cks-lab-07`. No API-server configuration or other node settings changed.
- Lab 07 learner attempt, duration, hints and weak areas: not assessed. This is selected kubelet hardening, not a full control-plane/CIS audit.

### 2026-09-21 — Lab 07 verification

- Read-only `./labs/07-control-plane-hardening/verify.sh`: 17 passed, zero failures, exit 0. Evidence: `.local/lab07-attempt-2026-09-21.log`.
- Disk and effective kubelet settings disable read-only serving and anonymous authentication. Other effective settings match the saved baseline; kubelet is active.
- TCP 10255 refused local and cross-node connections; anonymous HTTPS `/pods` returned 401. Authenticated configuration access, exec, logs and Service HTTP remained functional.
- All three nodes Ready, API healthy, original health fixtures preserved and health Pod Ready on the target worker.
- No failed requirements observed. Attempt duration and outside hints not recorded; no hints supplied during grading. This verifies selected kubelet controls, not an exhaustive control-plane audit.
- No node configuration, learner files or cluster resources modified during grading. Recovery state retained; no cleanup performed.

### 2026-09-24 — Lab 07 cleanup and Lab 08 preparation

- Lab 07 exercise, learner configuration and passing result committed and pushed as `698dcaa`; remote main verified. Original worker file/effective settings restored and owned namespace removed. Evidence: `.local/lab07-final-cleanup.log`.
- Lab 08 assesses selected cis-1.12 controls 4.1.9/4.1.10 using an original targeted scanner, not a full kube-bench execution. Upstream definitions pinned at `975ae0039595e2558f7cdbc19cc2a7502acacbfb`.
- Node mutation limited to mode and ownership of the existing kubelet configuration on `cks-worker2`; original metadata, hash, contents and container identity saved before mutation. No configuration edits or restarts needed.
- QA baseline: 8 passed / 2 failed. Repaired state: 10 / 0. World-readable 0444 regression: 9 / 1, confirming bitmask semantics. Scanner independently returned nonzero for the baseline and zero for the repaired state.
- Evidence: `.local/lab08-initial.log`, `.local/lab08-initial-scan.log`, `.local/lab08-passing.log`, `.local/lab08-passing-scan.log`, `.local/lab08-regression.log`, `.local/lab08-duplicate-setup.log`, `.local/lab08-rollback.log`.
- Duplicate setup refused; QA cleanup verified original metadata and content before removing its namespace/state. Shell syntax, Python parsing and Git whitespace checks passed.
- Fresh unsolved learner state prepared in `cks-lab-08`; recovery files retained in `.local/lab08-state/`. Learner attempt, duration, hints and weak areas unassessed. No claim of full CIS compliance or complete benchmark mapping for Kubernetes v1.37.

### 2026-09-24 — Lab 08 learner verification

- `./labs/08-cis-benchmarks/scan.sh`: both selected cis-1.12 controls passed on the target kubelet configuration file (mode 0600, numeric owner 0:0).
- `./labs/08-cis-benchmarks/verify.sh`: all 10 checks passed, exit 0. Original file contents and active config path preserved; kubelet, API, three nodes and target health Pod healthy; exec worked.
- No failed requirements observed in this selected-control assessment. Duration and outside hints not recorded; none provided during grading. No learner or cluster resources changed during verification.
- Passing these two checks does not establish complete CIS compliance.

### 2026-09-24 — Lab 08 cleanup and Lab 09 preparation

- Lab 08 source and passing result committed and pushed as `bdc825b`; remote main verified. Original worker file metadata and contents restored, and the owned namespace removed.
- Lab 09 uses the cached BusyBox digest approved at setup and two cluster-scoped ValidatingAdmissionPolicies plus bindings scoped to the exact lab namespace. Bindings begin in Audit; workload uses a mutable tag. The approved digest is saved in ignored `.local/lab09-state/` and exposed in the lab ConfigMap.
- QA: initial audit-only/tagged state 11 passed and 10 failed; enforced digest-pinned state 21 passed and 0 failed. Reverting the Pod binding to Audit caused 4 failures after admission propagation. A tag moved during QA, demonstrating why a saved digest must remain authoritative; the setup/recovery identity check was corrected.
- Evidence: `.local/lab09-initial.log`, `.local/lab09-passing.log`, `.local/lab09-regression.log`, `.local/lab09-duplicate-setup.log`, `.local/lab09-qa-cleanup.log`.
- Duplicate setup refused existing state. QA cleanup removed both owned bindings, both policies and QA namespace. Shell syntax, Python parsing and Git whitespace checks passed.
- Fresh learner namespace `cks-lab-09` prepared with audit-only bindings. Learner attempt, duration, hints and weak areas not assessed. Signature, vulnerability and SBOM verification are outside this exercise.

### 2026-09-24 — Lab 09 learner verification

- `./labs/09-supply-chain/verify.sh`: 21 passed, zero failures, exit 0. Evidence: `.local/lab09-attempt.log`.
- Both lab admission bindings enforce Deny in the intended namespace. Dry-run Pods and Deployments with the approved digest were accepted; mutable tags and unapproved regular or init containers were rejected.
- Deployment and running Pod reference the approved digest; runtime imageID matches. Rollout, Service response and original fixtures passed.
- No failed requirements observed. Duration and outside hints not recorded; none provided during grading. No learner or cluster resources changed during verification.
- Checks establish this lab's image identity and admission behavior, not image signature, vulnerability or SBOM validation.
