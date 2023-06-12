# etcd

`start.sh` is a helpful script that runs `etcd` using the necessary configurations. NOTE: You must provide a `.config` file (matching the structure of `.config.example`) with the names and hosts in your system. You must also supply a `../.THIS_NAME` file (which exists in root of project, mirroring `.THIS_NAME.example`) to declare which machine this node is.

It's important to have these ignore files so that different machines can join as different entities while still getting core logic from the same place in source control.

**IMPORTANT**

To actually interact with `etcd` from the command line you'll probably want to add 
```
export ETCDCTL_API=3`
```
to your `~/.bashrc`, otherwise you'll need to get that in your path on every session.