# Pod Security Admission

Read [TASK.md](TASK.md) for the 25-minute exercise.

```bash
./labs/04-pod-security/setup.sh
./labs/04-pod-security/verify.sh
./labs/04-pod-security/cleanup.sh
```

Setup creates an intentionally insecure Deployment, ConfigMap and Service in `cks-lab-04`, with privileged admission initially allowed. The learner controls only this namespace's Pod Security Admission labels and the Deployment security contexts. Namespace-scoped policy configuration requires namespace update permission; no cluster-wide admission changes are involved. Cleanup removes the namespace and those labels together.

The verifier reads resources, executes read-only runtime/HTTP checks and submits server-side dry-run Pod creations. No probe Pods are persisted. Positive admissions use the learner's template and running Pod specification; negative requests exercise privileged execution and privilege escalation violations. It requires PodSecurity-specific rejection text so unrelated API errors cannot pass negative tests. Audit and warning configuration is checked through labels; audit-log delivery is not tested. Verification does not restart or repair workloads.

Maintainer QA uses `CKS_LAB_NAMESPACE=cks-lab-04-qa` only. Passing patches are not stored in this lab.

Curriculum checked 2026-09-14: [CNCF curriculum](https://github.com/cncf/curriculum/tree/f6c7667265fef850daaf93b4e19e919552c67d8c), revision `f6c7667265fef850daaf93b4e19e919552c67d8c`, CKS v1.34 PDF; original practice for minimizing microservice vulnerabilities. The lab pins policy semantics to the installed Kubernetes v1.37, not an asserted exam version. Reference: [enforcing Pod Security Standards with namespace labels](https://kubernetes.io/docs/tasks/configure-pod-container/enforce-standards-namespace-labels/).
