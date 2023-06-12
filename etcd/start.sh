TOKEN=patroni-experiments
CLUSTER_STATE=new
NAME_1=pe1
NAME_2=pe2
NAME_3=pe3
HOST_1=10.51.140.91
HOST_2=10.51.140.76
HOST_3=10.51.140.84
CLUSTER=${NAME_1}=http://${HOST_1}:2380,${NAME_2}=http://${HOST_2}:2380,${NAME_3}=http://${HOST_3}:2380

if [[ "${THIS_NAME}" = "${NAME_1}" ]];
then
    THIS_IP=${HOST_1}
else
    if [[ "${THIS_NAME}" = "${NAME_2}" ]];
    then
        THIS_IP=${HOST_2}
    else
        THIS_IP=${HOST_3}
    fi
fi

etcd --data-dir=data --name ${THIS_NAME} \
	--initial-advertise-peer-urls http://${THIS_IP}:2380 \
	--listen-peer-urls http://${THIS_IP}:2380 \
	--advertise-client-urls http://${THIS_IP}:2379 \
	--listen-client-urls http://${THIS_IP}:2379,http://127.0.0.1:2379 \
	--initial-cluster ${CLUSTER} \
	--initial-cluster-state ${CLUSTER_STATE} \
	--initial-cluster-token ${TOKEN}
