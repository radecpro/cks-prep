# Secrets and sensitive data

Read [TASK.md](TASK.md) for the 25-minute exercise.

```bash
./labs/05-secrets/setup.sh
./labs/05-secrets/verify.sh
./labs/05-secrets/cleanup.sh
```

Setup creates a Deployment with an application and sidecar, a synthetic Secret, a script ConfigMap and a Service. Initial credentials are exposed through environment variables and broad volume mounts. The application supports file-based credential consumption already; preserve its script. Setup stops if the namespace exists.

Verification reads objects, container logs and process environments, and executes read-only file/HTTP probes. Credential comparisons are not printed. It inspects both the template and running Pod so an unrolled template change cannot pass. Log inspection covers available current-container logs, not historical or external log stores. It does not prove resistance to node compromise or malicious code. Kubernetes Secret projection is checked; etcd encryption at rest and credential rotation are separate exercises and are not assessed here.

Maintainer QA is restricted to `CKS_LAB_NAMESPACE=cks-lab-05-qa`; passing patches are not stored in this lab. Cleanup removes only the owned namespace.

Curriculum checked 2026-09-17: [CNCF curriculum](https://github.com/cncf/curriculum/tree/f6c7667265fef850daaf93b4e19e919552c67d8c), revision `f6c7667265fef850daaf93b4e19e919552c67d8c`, CKS v1.34 PDF; original practice for minimizing microservice vulnerabilities and managing sensitive data. References: [Secrets](https://kubernetes.io/docs/concepts/configuration/secret/) and [good practices](https://kubernetes.io/docs/concepts/security/secrets-good-practices/).
