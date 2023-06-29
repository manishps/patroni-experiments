import yaml
import sys
import os
from dataclasses import dataclass
from pe.exceptions import ConfigParseError
from pe.utils import ROOT_DIR

@dataclass
class AgentConfig:
    """
    An abstraction for agent in our system. It can be a VM, or entirely local
    with the right port combinations. Can either be a node (running patroni, etcd, etc...)
    or the proxy.
    """
    name: str
    host: str
    api_port: int

@dataclass
class NodeConfig(AgentConfig):
    """
    A node running patroni, etcd, postgres. Will participate in the fun stuff
    """
    patroni_port: int
    etcd_port: int
    pg_port: int

@dataclass
class ProxyConfig(AgentConfig):
    """
    The agent running the proxy. Has a special type and port to differentiate
    """
    proxy_port: int

@dataclass
class TopologyConfig:
    """
    A complete description of the environment used for the experiment(s)
    :param str config_file: Path (relative to module root) containing the config to use
    """
    def __init__(self, file_path):
        with open(os.path.join(ROOT_DIR, file_path), "r") as fin:
            config = yaml.safe_load(fin)
        self.my_name = config["my_name"]
        self.nodes = [NodeConfig(
            name=node["name"],
            host=node["host"],
            api_port=node["api_port"],
            patroni_port=node["patroni_port"],
            etcd_port=node["etcd_port"],
            pg_port=node["pg_port"]
        ) for node in config["nodes"]]
        self.proxy = ProxyConfig(
            name=config["proxy"]["name"],
            host=config["proxy"]["host"],
            api_port=config["proxy"]["api_port"],
            proxy_port=config["proxy"]["proxy_port"],
        )
        self.me: AgentConfig
        for node in self.nodes:
            if node.name == self.my_name:
                self.me = node
                break
        else:
            if self.proxy.name == self.my_name:
                self.me = self.proxy
            else:
                raise ConfigParseError("my_name doesn't correspond to a provided agent")

    def __str__(self):
        nodes_str = ""
        for node in self.nodes:
            nodes_str += f"\n  {node}"
        return \
            f"I am: {self.me}\n" + \
            f"Nodes: {nodes_str}\n" + \
            f"Proxy: {self.proxy}\n"

if __name__ == "__main__":
    topology = TopologyConfig("topology.example.yaml")
    print(topology)