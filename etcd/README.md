# etcd

`start.sh` stores the logic for actually booting up etcd. Notice, however, that this script references a variable THIS_NAME, that it does not define. That is because you are expected to define it elsewhere. I recommend creating `runner.sh` containing

```
THIS_NAME=pe[1|2|3]
export THIS_NAME
sh start.sh
```

and using `./runner.sh` to actually run it. You can also just manually export it