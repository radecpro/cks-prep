# 04: Enforce Pod Security Admission

Status: available
Time budget: 25 minutes
Context: kind-cks
Namespace: cks-lab-04
Prerequisites: repository kind cluster running Kubernetes v1.37 with Pod Security Admission; kubectl and Python 3.

## Scenario

The status service runs in a namespace that permits privileged workloads. Migrate it to Restricted Pod Security Standards and protect future admissions while retaining a healthy application.

## Requirements

1. Configure namespace enforcement, warning and audit modes to Restricted, each pinned to `v1.37`.
2. Update Deployment `status` so its template and running Pods comply with that standard. Run the web process as UID and GID 10000.
3. Finish with one Ready, available replica from a completed rollout. Preserve image, command, arguments, labels, readiness probe, Service, ConfigMap content, volumes and mounts. The Service must still return `cks-lab-04-ready` over HTTP on port 8080.
4. Fresh compliant Pods must be admissible. Fresh privileged Pods and Pods allowing privilege escalation must be rejected by Pod Security Admission.
5. Change only Pod Security Admission labels on this namespace and security contexts in the Deployment. Retain its ownership label. Do not add exemptions or change cluster-wide admission configuration. Replacing Pods through the Deployment rollout is allowed.

## Start

From the repository root, run `./labs/04-pod-security/setup.sh` if not already prepared. Setup refuses an existing namespace.

## Verification

Run `./labs/04-pod-security/verify.sh`. It inspects namespace labels, workload and runtime state, probes HTTP, and submits non-persistent server-side dry-run Pod admission requests. It does not repair resources. Failed requirements produce exit code 1.

## Cleanup

Run `./labs/04-pod-security/cleanup.sh`. This removes the owned namespace, including its admission labels and workloads. No cluster-wide changes are needed.
