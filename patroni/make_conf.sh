cp TEMPLATE.yml conf.yml
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
sed -i "s/<THIS_NAME>/$THIS_NAME/" conf.yml
sed -i "s/<THIS_IP>/$THIS_IP/" conf.yml