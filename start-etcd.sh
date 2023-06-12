TOKEN=patroni-experiments
CLUSTER_STATE=new
NAME_1=pe1
NAME_2=pe2
NAME_3=pe3
HOST_1=10.51.140.91
HOST_2=10.51.140.76
HOST_2=10.51.140.84
CLUSTER=${NAME_1}=http://${HOST_1}:2380,${NAME_2}=http://${HOST_2}:2380,${NAME_3}=http://${HOST_3}:2380

THIS_NAME=${NAME_3}
THIS_IP=${HOST_3}

etcd --data-dir=data.etcd --name ${THIS_NAME} \
	--initial-advertise-peer-urls http://${THIS_IP}:2380 \
	--listen-peer-urls http://${THIS_IP}:2380 \
	--advertise-client-urls http://${THIS_IP}:2379 \
	--listen-client-urls http://${THIS_IP}:2379,http://127.0.0.1:2379 \
	--initial-cluster ${CLUSTER} \
	--initial-cluster-state ${CLUSTER_STATE} \
	--initial-cluster-token ${TOKEN}
