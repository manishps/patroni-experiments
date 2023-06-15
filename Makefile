proxy:
	cd haproxy && ./start-haproxy.sh

api:
	cd runner && python3 node_server.py&

node-etcd:
	cd etcd && ./start-etcd.sh

node-patroni:
	cd patroni && ./start-patroni.sh 


