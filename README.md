# CKS preparation

Hands-on preparation for an experienced Kubernetes / Cloud engineer. Work through focused labs, record evidence and weak areas, then move to mixed timed scenarios.

## Start here

```bash
./scripts/doctor.sh
./scripts/cluster-create.sh
./scripts/calico-install.sh
./scripts/cluster-status.sh
./scripts/cluster-verify.sh
```

These commands create a local cluster named `cks` with one control plane and two workers. Kubeconfig is stored in `.local/kubeconfig`; scripts explicitly target `kind-cks` and do not change your default kubeconfig. Docker must be running. Cluster creation refuses to replace an existing `cks` cluster.

For interactive practice in the current shell:

```bash
export KUBECONFIG="$PWD/.local/kubeconfig"
kubectl --context kind-cks get nodes -o wide
```

The default node image comes from your installed kind release. For repeatable runs, select a supported image (preferably with its digest) from the [kind releases](https://github.com/kubernetes-sigs/kind/releases), then set `KIND_NODE_IMAGE` when invoking `cluster-create.sh`. Verify the exam Kubernetes version against the Linux Foundation before choosing it; the local default is not a claim of exam parity.

Calico is pinned to v3.32.2 using the manifest installation in the [official kind guide](https://docs.tigera.io/calico/latest/getting-started/kubernetes/kind), checked 2026-09-07. Its manifest is downloaded into `.local/` and applied to the lab cluster. The configured pod CIDR is `192.168.0.0/16`; check for LAN/VPN overlap before creation and adjust the CNI pool consistently if changing it. Nodes become ready after CNI installation. NetworkPolicy labs must additionally prove both allowed and blocked traffic; healthy CNI pods alone do not prove enforcement.

## Repository map

| Path | Purpose |
| --- | --- |
| `cluster/` | kind topology and cluster notes |
| `scripts/` | workstation checks, cluster creation, CNI installation and status |
| `curriculum/` | six domain study checklists and authoritative references |
| `labs/` | numbered focused labs; Labs 01–03 available, remaining labs planned |
| `scenarios/` | mixed troubleshooting scenarios |
| `mocks/` | timed multi-task practice and scoring |
| `templates/` | task and review templates |
| `progress.md` | attempts, elapsed time, hints and weak areas |
| `cheatsheet.md` | command and documentation lookup notes |

## Practice workflow

1. Open `labs/01-security-context/TASK.md` for the first exercise. Setup and automated grading are provided; no solution is included.
2. Run setup, read the task, start a timer and solve it yourself.
3. Run verification. Ask for a read-only review; fixes require a separate request.
4. Record results in `progress.md`, including failed requirements and a retry date.

Keep task requirements separate from grading implementation. Verification must check runtime behavior where relevant, fail on unmet requirements, and never repair the solution. No learner exercises or assessments have been executed. The cluster smoke test checks infrastructure only.

kind on macOS runs container nodes inside Docker's Linux environment. Use a dedicated Linux VM for host/kernel labs when AppArmor, runtime detection or OS hardening cannot be represented faithfully.

## Sources of truth

- [CNCF curriculum](https://github.com/cncf/curriculum): use the current CKS curriculum before authoring tasks; study checklists here are planning aids, not an official syllabus.
- [Linux Foundation CKS](https://training.linuxfoundation.org/certification/certified-kubernetes-security-specialist/): verify exam version, format and candidate rules before timed preparation.
- [Kubernetes documentation](https://kubernetes.io/docs/): practice finding the relevant task and API reference pages.

## Validation and teardown

Run `for script in scripts/*.sh; do bash -n "$script" || exit; done` for syntax validation; use `./scripts/doctor.sh` for live prerequisites. There is no application build or CI suite.

To discard all lab work, explicitly run `kind delete cluster --name cks`. This destroys that cluster; recreation uses the start commands above. Never commit kubeconfigs, tokens, keys or real secrets. Use synthetic data in labs.

## Verified environment (2026-09-07)

The cluster is running Kubernetes v1.37.0 with Calico v3.32.2. API readiness, all three nodes, system pods, DNS, cross-worker Service traffic and NetworkPolicy ingress deny/allow checks passed. Exact node image identity is recorded in `progress.md`. Exam-version alignment has not been verified.

`./scripts/cluster-verify.sh` creates the temporary `cks-lab-smoke` namespace, runs traffic checks, then deletes it. It refuses to proceed if that namespace already exists. The smoke test does not certify every security feature or host/kernel lab prerequisite.
