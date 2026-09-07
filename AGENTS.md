# Repository Guidelines

This repository holds CKS practice materials, Bash tooling and a disposable kind cluster. The learner is an experienced Cloud/DevOps engineer; focus on security tasks and measurable outcomes.

## Training boundaries

- Do not reveal solutions or add hints unless requested. Prepare intentionally insecure or broken lab environments, then let the learner solve them.
- During grading, run verification and inspect resources without repairing the solution. Report failed requirements and record evidence and weak areas in `progress.md`.
- All Kubernetes scripts must use the repository kubeconfig and explicit `kind-cks` context through `scripts/common.sh`. Do not rely on the ambient context.
- Scope workloads to `cks-lab-NN`. Document cluster-wide changes and rollback before running a lab that needs them. Never delete or replace an existing cluster implicitly.
- Keep real credentials and kubeconfig out of Git; `.local/` is ignored. Use synthetic secret values.

## Commands and structure

- `./scripts/doctor.sh` checks installed tools, Docker and the lab cluster when configured.
- `./scripts/cluster-create.sh` creates the three-node cluster; `./scripts/calico-install.sh` installs its CNI.
- `./scripts/cluster-status.sh` inspects cluster state.
- See @README.md for environment selection, interactive commands and teardown; @cluster/kind.yaml defines the topology.
- `labs/NN-topic/` contains focused exercises; `scenarios/` and `mocks/` hold mixed practice. Planning directories are not runnable labs.

## Authoring and validation

Use @templates/TASK.md for learner-facing requirements. Each implemented lab needs executable `setup.sh` and `verify.sh`, prerequisites and scoped cleanup. Keep setup, task statements and grading separate. Verification must return nonzero on unmet requirements and check functionality as well as configuration; NetworkPolicy needs positive and negative traffic checks.

Use Bash with `set -euo pipefail`, quoted paths and two-space YAML indentation. Run `bash -n` on every changed shell script. Live-test implemented labs against the intended cluster, including the initial failing state and a known passing state in disposable test resources. Report checks not run. There is no application build or CI suite.

Check the current CNCF curriculum before adding objectives; record its revision. Use @templates/REVIEW.md for attempt evidence. Do not mark skills mastered without observed results. Host/kernel exercises may require a Linux VM; document unsupported behavior instead of claiming kind provides equivalent coverage.
