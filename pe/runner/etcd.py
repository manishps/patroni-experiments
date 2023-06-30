import os
from pe.config.parse import NodeConfig, TopologyConfig
from pe.exceptions import BootError
from pe.utils import kill_process_on_port, ROOT_DIR
from typing import Union

def etcd_process(my_name: str, config: TopologyConfig):
    # Verify there's a node in config with this name
    me: Union[NodeConfig, None] = None
    for node in config.nodes:
        if node.name == my_name:
            me = node
            break
    if me == None:
        raise BootError("Etcd misconfigured for" + my_name)
    
    # Kill any programs on needed ports
    for port in [me.etcd_port, me.etcd_port + 1]:
        kill_process_on_port(port)

    lines = ["etcd"]

    # Output data pe/../data/<name>
    lines.append(f"--data-dir {ROOT_DIR}/../data/etcd/{my_name}")
    # Name ourselves
    lines.append(f"--name {my_name}")
    # Advertise ourselves to peers
    lines.append(f"--initial-advertise-peer-urls http://{me.host}:{me.etcd_port + 1}")
    # Listen for peers on the same port
    lines.append(f"--listen-peer-urls http://{me.host}:{me.etcd_port + 1}")
    # Advertise for clients on a different port
    lines.append(f"--advertise-client-urls http://{me.host}:{me.etcd_port}")
    # Listen for clients on that^ port
    lines.append(f"--listen-client-urls http://{me.host}:{me.etcd_port},http://127.0.0.1:{me.etcd_port}")

    # Construct the cluster
    CLUSTER = ""
    for node in config.nodes:
        CLUSTER += f"{node.name}=http://{node.host}:{node.etcd_port + 1},"
    CLUSTER = CLUSTER[:-1]
    lines.append(f"--initial-cluster {CLUSTER}")
    # Set the cluster state
    lines.append(f"--initial-cluster-state new")
    # Set the cluster token
    lines.append(f"--initial-cluster-token patroni-experiments")

    # Enable v2 for local if needed
    lines.append(f"--enable-v2=true")
    # Silence
    lines.append(f"--log-outputs /dev/null")

    COMMAND = " ".join(lines)
    os.system(COMMAND)
