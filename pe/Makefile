proxy:
	cd haproxy && ./start-haproxy.sh

api:
	./kill.sh && source venv/bin/activate && cd runner && python3 node_server.py&

reset-data:
	rm -rf etcd/data && rm -rf patroni/data

node-etcd:
	cd etcd && ./start-etcd.sh

node-patroni:
	cd patroni && ./start-patroni.sh 

experiment:
	cd runner && python3 exprunner.py

viewer:
	cd runner && python3 viewer.py

kill:
	./kill.sh

refresh:
	source venv/bin/activate && python3 refresh.py