# 05: Minimize Secret exposure

Status: available
Time budget: 25 minutes
Context: kind-cks
Namespace: cks-lab-05
Prerequisites: running repository kind cluster; kubectl and Python 3.

## Scenario

The payments Pod has an application container and an observer sidecar. Both receive credentials they do not need. Limit exposure while keeping the application available. All credential values are synthetic.

## Requirements

1. Container `app` must read only the `password` key of Secret `db-credentials`, as `/etc/db/password`. Keep using the existing `credentials` Secret volume. Its file must be readable by the existing application identity, with runtime mode exactly `0440`, and the mount must be read-only without subPath.
2. The `admin-token` key must not be projected into any container. Container `observer` must have no Secret volume mounts or credentials available as files.
3. Remove all `env` and `envFrom` entries from both containers. Credential values must not appear in process environments or container logs, or be copied into ConfigMaps, commands or arguments.
4. Preserve the Secret and its two original keys/values. Preserve ConfigMap `app-script`, the Service, container names/images/commands, security contexts, Pod labels, readiness probe and one replica. Preserve the script mount. Do not add containers or volumes, enable token automount, or change service accounts.
5. Complete the rollout with one Ready Pod containing both containers. Service `payments:8080` must return `cks-lab-05-ready`.
6. Change only Deployment `payments` environment entries, the `credentials` volume's Secret settings, and container mount settings needed to meet these requirements. Do not change cluster configuration or RBAC.

## Start

If not already prepared, run `./labs/05-secrets/setup.sh` from the repository root. Setup refuses an existing namespace.

## Verification

Run `./labs/05-secrets/verify.sh`. It checks the template and live Pod, mounted file content and permissions, environment/log exposure, and Service response without repairing resources. Failed checks return nonzero. The file content is compared without printing it.

## Cleanup

Run `./labs/05-secrets/cleanup.sh` to delete the owned namespace and its synthetic data. No cluster-wide changes are involved.
