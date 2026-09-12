# 02: Reduce the observer's API permissions

Time budget: 20 minutes
Context: `kind-cks`
Namespace: `cks-lab-02`

## Scenario

An observer workload was deployed with excessive Kubernetes API access. Its dedicated identity is also used by an external diagnostic process. That process needs a small read-only permission set; this placeholder workload itself does not need an API token mounted.

## Requirements

1. ServiceAccount `inspector` must have exactly these resource permissions within this namespace:
   - Get, list and watch Pods.
   - Get Pod logs.
   - Get only ConfigMap `app-config` by name; no listing or watching ConfigMaps.
2. Grant no other resource permissions: no Secrets, writes, exec/attach, token creation, RBAC administration, access to other namespaces or cluster-scoped resources. Keep the cluster's standard API discovery permissions unchanged.
3. Use the existing Role and RoleBinding named `observer-access`. The binding must grant access only to ServiceAccount `inspector` in this namespace. Do not create extra Roles or bindings.
4. The namespace's `default` ServiceAccount must lose the resource access introduced by this lab.
5. Explicitly disable automatic API token mounting on ServiceAccount `inspector`. Deployment `observer` and its running Pod must use this identity without mounting an API token.
6. Leave one available replica of `observer` with the original `worker` container, image, command and arguments. Do not add containers or volumes. Keep both ConfigMaps and the synthetic Secret unchanged.

Modify only this lab's namespace-scoped RBAC, ServiceAccount and Deployment. Do not modify cluster-scoped resources or other namespaces. Wait for a completed rollout before grading.

## Start and verification

The environment may already be prepared. `./setup.sh` creates a fresh namespace and refuses to overwrite an existing attempt. Requires the repository cluster, kubectl and Python 3.

Inspect the environment, start your timer, and solve using kubectl and documentation. Run `./verify.sh` when finished. It checks positive and negative authorization, RBAC structure, workload identity, rollout and token exposure without changing your solution.

## Cleanup / restart

`./cleanup.sh` deletes only this lab namespace, including your work. Run setup afterward only to intentionally restart.
