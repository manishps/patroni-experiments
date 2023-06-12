# etcd

`start.sh` stores the logic for actually booting up etcd. Notice, however, that this script references a variable THIS_NAME, that it does not define. That is because you are expected to define it elsewhere. I recommend creating `runner.sh` containing

```
THIS_NAME=pe[1|2|3]
export THIS_NAME
sh start.sh
```

and using `./runner.sh` to actually run it. You can also just manually export it

**IMPORTANT**

To actually interact with `etcd` from the command line you'll probably want to add 
```
export ETCDCTL_API=3`
```
to your `~/.bashrc`, otherwise you'll need to get that in your path on every session.