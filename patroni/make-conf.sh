cp TEMPLATE.yml conf.yml
THIS_NAME=$(cat ../.THIS_NAME)
NAME_1=$(cat ../.config/.NAME_1)
NAME_2=$(cat ../.config/.NAME_2)
NAME_3=$(cat ../.config/.NAME_3)
HOST_1=$(cat ../.config/.HOST_1)
HOST_2=$(cat ../.config/.HOST_2)
HOST_3=$(cat ../.config/.HOST_3)
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
sed -i "s/<THIS_NAME>/$THIS_NAME/" conf.yml
sed -i "s/<THIS_IP>/$THIS_IP/" conf.yml