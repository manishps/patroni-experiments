proxy:
	cd haproxy && ./start-haproxy.sh

api:
	source venv/bin/activate && cd runner && python3 node_server.py&

node-etcd:
	cd etcd && rm -rf data && ./start-etcd.sh

node-patroni:
	cd patroni && rm -rf data && ./start-patroni.sh 

experiment:
	cd runner && python3 exprunner.py
