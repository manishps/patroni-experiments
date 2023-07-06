import multiprocessing
import subprocess
from abc import ABC, abstractmethod
from typing import Union
import yaml
import os
import shlex
from pe.config.parse import NodeConfig, TopologyConfig
from pe.exceptions import BootError
from pe.utils import kill_process_on_port, ROOT_DIR


class AbstractCMDController(ABC):
    """
    An abstract class for controlling something run from the command line.
    Useful because patroni, etcd, haproxy are all things that we launch from
    the command line, but would like to have better control over (better
    than tossing around kill -9s all the time)
    """
    def __init__(self):
        self.process: Union[subprocess.Popen, None] = None
        self.tmp_files: list[str] = []

    def start(self, _):
        if self.process != None:
            raise BootError("Tried to start an already started controller")

    def stop(self):
        if self.process == None:
            raise BootError("Tried to stop a non-started controller")
        self.process.terminate()
        for file in self.tmp_files:
            os.system(f"rm {file}")


class EtcdController(AbstractCMDController):
    """
    A class for managing an etcd instance launched from the command line
    """
    def start(self, config: dict):
        super().start(config)

        my_name: str = config["my_name"]
        top_config: TopologyConfig = config["topology"]
        # Verify there's a node in config with this name
        me: Union[NodeConfig, None] = None
        for node in top_config.nodes:
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
        lines.append(f"--data-dir {ROOT_DIR}/data/etcd/{my_name}")
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
        for node in top_config.nodes:
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
        self.process = subprocess.Popen(shlex.split(COMMAND))
    
    def stop(self):
        super().stop()


class PatroniController(AbstractCMDController):
    """
    A class for managing a patroni instance launched from the command line
    """
    def start(self, config: dict):
        super().start(config)

        # Kill any programs on needed ports
        for conn_str in [config["postgresql"]["connect_address"], config["restapi"]["connect_address"]]:
            port = int(conn_str.split(":")[1])
            kill_process_on_port(port)

        config_file = os.path.join(ROOT_DIR, "runner", "tmp", "patroni_" + config["name"] + ".yml")
        with open(config_file, "w") as fout:
            fout.write(yaml.safe_dump(config))
        self.tmp_files.append(config_file)
        self.process = subprocess.Popen(shlex.split(f"patroni {config_file}"))
    
    def stop(self):
        super().stop()


class ProxyController(AbstractCMDController):
    """
    A class for managing the proxy instance launched from the command line
    """
    def start(self, config: str):
        super().start(config)

        config_file = os.path.join(ROOT_DIR, "runner", "tmp", "proxy" + ".cfg")
        with open(config_file, "w") as fout:
            fout.write(config)
        self.tmp_files.append(config_file)
        self.process = subprocess.Popen(shlex.split(f"haproxy -f {config_file}"))

    def stop(self):
        super().stop()