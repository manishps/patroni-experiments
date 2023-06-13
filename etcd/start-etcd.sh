TOKEN=patroni-experiments
CLUSTER_STATE=new
NAME_1=$(cat ../.config/.NAME_1)
NAME_2=$(cat ../.config/.NAME_2)
NAME_3=$(cat ../.config/.NAME_3)
HOST_1=$(cat ../.config/.HOST_1)
HOST_2=$(cat ../.config/.HOST_2)
HOST_3=$(cat ../.config/.HOST_3)
CLUSTER=${NAME_1}=http://${HOST_1}:2380,${NAME_2}=http://${HOST_2}:2380,${NAME_3}=http://${HOST_3}:2380

THIS_NAME=$(cat ../.THIS_NAME)

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
