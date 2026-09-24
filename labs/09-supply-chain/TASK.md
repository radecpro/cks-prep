# 09: Pin and enforce an approved image

Status: available
Time budget: 20 minutes
Context: kind-cks
Namespace: cks-lab-09
Prerequisites: running kind cluster with ValidatingAdmissionPolicy v1 and Docker, kubectl, Python 3. Read the cluster-scoped change and rollback section in README.md first.

## Scenario

The status workload uses a mutable image tag. An approved image digest is recorded in ConfigMap `release-metadata`, but two admission bindings only audit noncompliant image references. Pin the workload and enforce that approved image for both Pods and Deployments in this namespace.

## Requirements

1. Change Deployment `status` to the exact canonical digest reference recorded as `approvedImage` in ConfigMap `release-metadata`. Keep one Ready replica and the original Service response `cks-lab-09-ready`.
2. Change the two lab-owned ValidatingAdmissionPolicyBindings from audit-only to `Deny`, so new Pods and Deployments in this namespace using any other image reference are rejected at admission. New objects using the approved digest must be accepted. Include a noncompliant sidecar or init container in the rejection scope.
3. Keep both policies and their bindings scoped to this namespace only. Preserve the existing policy expressions, resource rules, failure policy, labels and ownership. Do not create extra policies or bypass the check by changing namespace labels.
4. Preserve the ConfigMap values, status page, Service, container image identity at runtime, Pod labels, commands, ports, readiness probe, placement and disabled token automount. Change only the Deployment image field and the lab binding `validationActions`.
5. Do not change other namespaces, admission policies, registry contents or cluster configuration.

## Start

Run `./labs/09-supply-chain/setup.sh` only if the lab is not already prepared. It creates two cluster-scoped policies and bindings; the rollback is documented in README.md. Setup refuses existing lab state or namespace.

## Verification

Run `./labs/09-supply-chain/verify.sh`. It reads resources and uses non-persistent server-side dry-run admissions for allowed and denied Pods/Deployments. It does not repair resources and returns nonzero on unmet requirements.

## Cleanup

Run `./labs/09-supply-chain/cleanup.sh` to remove only lab-owned policies/bindings and namespace. It retains recovery state if a cleanup step fails.
