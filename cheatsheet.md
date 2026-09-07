# Command and documentation notebook

Add commands that saved time during your own attempts. Keep complete lab solutions out of this file.

## Context and inspection

```bash
export KUBECONFIG="$PWD/.local/kubeconfig" # from repo root
kubectl config current-context
kubectl --context kind-cks get nodes
kubectl explain pod.spec.securityContext
kubectl explain pod.spec.containers.securityContext
kubectl api-resources
kubectl auth can-i --list -n cks-lab-01
```

## Personal notes

| Topic | Useful command / documentation URL | When to use it |
| --- | --- | --- |

## Mistakes to avoid

Record repeated errors after grading, with a short correction in your own words.
