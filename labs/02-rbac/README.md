# RBAC and ServiceAccounts

Status: implemented. Start with [TASK.md](TASK.md). No solution is included.

- `setup.sh` creates a fresh namespace, ServiceAccount, overprivileged Role/binding, sample configuration and observer workload. It refuses an existing namespace.
- `verify.sh` grades configuration, API authorization and runtime token exposure using kubectl and Python 3.
- `cleanup.sh` deletes only the namespace bearing this lab's ownership label.
- `resources.py` generates deliberately insecure initial resources. Secret data is synthetic.

Default namespace: `cks-lab-02`. Maintainer validation accepts `CKS_LAB_NAMESPACE=cks-lab-02-qa`; other overrides are rejected.

## Curriculum and scope

Maps to Cluster Hardening: RBAC and ServiceAccount access reduction. Checked 2026-09-11 against [CNCF revision f6c7667](https://github.com/cncf/curriculum/blob/f6c7667265fef850daaf93b4e19e919552c67d8c/cks/README.md). Locally authored practice, not official exam questions.

## Grader design

Checks the exact permissions of the existing Role, its binding subjects, positive and negative authorization using ServiceAccount impersonation with standard groups, Deployment/Pod identity, token automount settings and the runtime token path. Authorization requests do not execute the prohibited actions. It also checks rollout completion and unchanged sample data.

No persistent cluster resources or workload files are modified during verification. `kubectl auth can-i` submits authorization reviews; runtime checks use read-only exec. Additional Roles/bindings and containers/volumes are excluded by the task to keep grading bounded. This is not an exhaustive audit of pre-existing cluster authorization or arbitrary hidden credentials.

## Maintainer validation

On Kubernetes v1.37.0: initial state fails (18 checks), temporary passing state passes all 42 checks. Regression tests cover excess Secret access and automatic token mounting. Setup refuses to overwrite an existing attempt. QA uses a separate disposable namespace; no passing fixture is retained.
