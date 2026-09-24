# Approved image and admission

Read [TASK.md](TASK.md) for the 20-minute exercise.

## Cluster-scoped changes and rollback

Setup creates two `ValidatingAdmissionPolicy` resources and two `ValidatingAdmissionPolicyBinding` resources with names prefixed by the lab namespace. They match only Pods and Deployments in the exact lab namespace. The bindings initially have `validationActions: [Audit]`, so the insecure workload can run while findings are observable. The policies validate every regular and init container against one approved image digest. No other cluster-scoped resources are changed.

Setup first verifies the target kind cluster, that none of those resource names or the namespace exist, and that the expected BusyBox tag and digest are cached on `cks-worker2`. It records object names, container identity and approved digest in ignored `.local/lab09-state/` before creating resources. The workload is pinned to that worker. The approved digest is also placed in a lab ConfigMap.

Cleanup checks the saved identity and each resource's `cks-prep/lab=09` ownership label before deleting bindings, policies and the lab namespace. It then removes the recovery state. If cleanup fails, keep `.local/lab09-state/` and rerun cleanup. Never delete similarly named unowned policies. The cluster-scoped resources cannot affect other namespaces because their binding `namespaceSelector` uses the exact namespace name label. Do not run the QA and learner variants concurrently.

```bash
./labs/09-supply-chain/setup.sh
./labs/09-supply-chain/verify.sh
./labs/09-supply-chain/cleanup.sh
```

The grader checks the live Deployment/Pod, exact policy scope and dry-run admission behavior. A positive dry run proves only API admission, not registry signature verification or vulnerability status. The runtime imageID check proves this cluster ran the approved digest, not who built or signed it. Pulling a cached digest may still require registry access on a different node. Scanning, SBOMs, signatures and attestations are separate supply-chain exercises.

Maintainer QA uses only `CKS_LAB_NAMESPACE=cks-lab-09-qa`, tests failing/passing/regression states, then removes all QA resources. Passing patches are not stored in the exercise.

Curriculum checked 2026-09-24: [CNCF curriculum](https://github.com/cncf/curriculum/tree/f6c7667265fef850daaf93b4e19e919552c67d8c), revision `f6c7667265fef850daaf93b4e19e919552c67d8c`, CKS v1.34 PDF. Original practice for supply-chain security. References: [Kubernetes images](https://kubernetes.io/docs/concepts/containers/images/) and [Validating Admission Policy](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/).
