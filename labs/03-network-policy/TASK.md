# 03: Isolate application traffic

Status: available
Time budget: 25 minutes
Context: kind-cks
Namespace: cks-lab-03
Prerequisites: running three-node kind cluster with Calico; kubectl and Python 3.

## Scenario

Four workloads share an unrestricted namespace. The frontend needs the API, but unrelated workloads must be isolated. All four Pods serve HTTP on TCP 8080 and 9090 for traffic testing.

## Requirements

1. Establish namespace-wide default denial of both ingress and egress, including future Pods.
2. Allow only `app=frontend` Pods to reach `app=api` Pods on TCP 8080 within this namespace. Access through Service `api:8080` and directly to the API Pod must work.
3. Allow every Pod in this namespace to query the cluster CoreDNS Pods in `kube-system` on UDP and TCP 53. Scope this exception to those DNS Pods.
4. Deny every other connection between distinct lab Pods, including frontend → API TCP 9090. Deny all other ingress and egress except platform traffic exempt from Kubernetes NetworkPolicy enforcement.
5. Preserve all four Ready Pods, their labels, placement, images, commands and HTTP listeners, and the existing Service. Change only NetworkPolicy resources in `cks-lab-03`. Do not change other namespaces or cluster configuration.

## Start

From the repository root, run `./labs/03-network-policy/setup.sh` only if the lab has not already been prepared. Setup refuses an existing namespace.

## Verification

Run `./labs/03-network-policy/verify.sh`. It checks isolation configuration, fixture integrity, DNS, allowed Service/direct traffic and blocked traffic on both HTTP ports. It returns nonzero on failure and does not repair resources.

## Cleanup

Run `./labs/03-network-policy/cleanup.sh` to remove the owned lab namespace.
