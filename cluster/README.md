# Cluster

`kind.yaml` defines the disposable `cks` cluster. Run scripts from the repository; they resolve paths independently of the current directory. Creation and Calico installation are separate so a failed CNI install can be retried without rebuilding nodes.

Version choices and setup commands are in the root README. Record the actual node image and Kubernetes version in `progress.md` after bootstrap. The creation script records the node container image identifiers in `.local/node-images.txt`.

To inspect the control plane after creation:

```bash
docker exec -it cks-control-plane bash
ls /etc/kubernetes/manifests/
cat /var/lib/kubelet/config.yaml
crictl ps
```

Do not assume these container nodes reproduce a full Linux VM. Keep backups before control-plane configuration labs and document recovery steps in each task.
