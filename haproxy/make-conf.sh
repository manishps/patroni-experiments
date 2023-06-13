cp TEMPLATE.cfg conf.cfg

NAME_1=$(cat ../.config/.NAME_1)
NAME_2=$(cat ../.config/.NAME_2)
NAME_3=$(cat ../.config/.NAME_3)
HOST_1=$(cat ../.config/.HOST_1)
HOST_2=$(cat ../.config/.HOST_2)
HOST_3=$(cat ../.config/.HOST_3)

sed -i "s/<NAME_1>/$NAME_1/" conf.cfg
sed -i "s/<NAME_2>/$NAME_2/" conf.cfg
sed -i "s/<NAME_3>/$NAME_3/" conf.cfg
sed -i "s/<HOST_1>/$HOST_1/" conf.cfg
sed -i "s/<HOST_2>/$HOST_2/" conf.cfg
sed -i "s/<HOST_3>/$HOST_3/" conf.cfg