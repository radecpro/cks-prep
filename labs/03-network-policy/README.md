# NetworkPolicy

Read [TASK.md](TASK.md) for the 25-minute exercise. Setup creates four Pods and one Service in `cks-lab-03`, initially without NetworkPolicies. No cluster-wide changes are required.

From the repository root:

```bash
./labs/03-network-policy/setup.sh
./labs/03-network-policy/verify.sh
./labs/03-network-policy/cleanup.sh
```

The grader reads Kubernetes resources and executes DNS/HTTP probes in existing Pods. It makes no Kubernetes resource changes. Negative HTTP tests require healthy local listeners and two timed-out connection attempts, avoiding false passes from broken applications or failed exec. It checks namespace-wide deny policies and tests every directed pair of distinct fixture Pods on TCP 8080/9090. This bounded matrix does not prove isolation against every external endpoint or all possible additional policy grants; inspect policies against the full task requirements too. In particular, review namespace and DNS peer scope, extra grants, and ingress and egress independently: one direction blocking traffic can mask an overly permissive policy in the other direction. DNS checks cover UDP resolution and TCP connection establishment, not a full TCP DNS response. Self-traffic and node-exempt traffic are outside the matrix.

Maintainer QA uses only `CKS_LAB_NAMESPACE=cks-lab-03-qa`; it is separate from the learner attempt. Passing configurations are not stored in the exercise.

Curriculum checked 2026-09-12: [CNCF curriculum](https://github.com/cncf/curriculum/tree/f6c7667265fef850daaf93b4e19e919552c67d8c), revision `f6c7667265fef850daaf93b4e19e919552c67d8c`, CKS v1.34 PDF; Cluster Setup / network security practice. These are original practice requirements, not exam questions. Semantics reference: [Kubernetes Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/).
