proxy:
	cd haproxy && ./start-haproxy.sh

node-etcd:
	cd etcd && ./start-etcd.sh

node-patroni:
	cd patroni && ./start-patroni.sh 
