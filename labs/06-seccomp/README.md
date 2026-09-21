# seccomp

Read [TASK.md](TASK.md) for the 15-minute exercise.

```bash
./labs/06-seccomp/setup.sh
./labs/06-seccomp/verify.sh
./labs/06-seccomp/cleanup.sh
```

Setup creates an intentionally unconfined two-container Deployment, a ConfigMap and a Service. This exercise tests RuntimeDefault configuration, container overrides, rollout completion and live process filter mode. Grading is read-only: resource inspection, `/proc/1/status` reads and HTTP requests.

Runtime support is tested in the isolated `cks-lab-06-qa` namespace before learner setup. Kind runs Linux containers in Docker Desktop's Linux VM; this does not imply macOS provides seccomp. Filter mode confirms filtering is active, but does not identify the complete syscall allowlist or prove which particular syscall a filter blocks. The grader combines runtime evidence with explicit Kubernetes profile configuration. No custom Localhost profiles, syscall-specific denial tests or node-level default configuration are assessed. Those need separate exercises and, where appropriate, a Linux VM.

Only namespace-owned resources are changed. Cleanup requires the ownership label and removes the namespace. Passing QA patches are not stored in the exercise.

Curriculum checked 2026-09-20: [CNCF curriculum](https://github.com/cncf/curriculum/tree/f6c7667265fef850daaf93b4e19e919552c67d8c), revision `f6c7667265fef850daaf93b4e19e919552c67d8c`, CKS v1.34 PDF; original practice for system hardening and reducing container attack surface. References: [seccomp tutorial](https://kubernetes.io/docs/tutorials/security/seccomp/) and [seccomp field semantics](https://kubernetes.io/docs/reference/node/seccomp/).
