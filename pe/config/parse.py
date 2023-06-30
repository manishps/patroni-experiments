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
    or the proxy
    """
    name: str
    host: str
    api_port: int

    @property
    def replacements(self) -> list[tuple[str, str]]:
        """
        Helper function for generating a list of keywords to look for while
        templating configuration files
        """
        return [
            ("name", self.name),
            ("host", self.host),
            ("api_port", str(self.api_port)),
        ]


@dataclass
class NodeConfig(AgentConfig):
    """
    A node running patroni, etcd, postgres. Will participate in the fun stuff
    """
    patroni_port: int
    etcd_port: int
    pg_port: int

    @property
    def replacements(self) -> list[tuple[str, str]]:
        """
        Helper function for generating a list of keywords to look for while
        templating configuration files
        """
        return [
            ("patroni_port", str(self.patroni_port)),
            ("etcd_port", str(self.etcd_port)),
            ("pg_port", str(self.pg_port)),
        ] + super().replacements

@dataclass
class ProxyConfig(AgentConfig):
    """
    The agent running the proxy. Has a special type and port to differentiate
    """
    proxy_port: int
    
    @property
    def replacements(self) -> list[tuple[str, str]]:
        """
        Helper function for generating a list of keywords to look for while
        templating configuration files
        """
        return [
            ("proxy_port", str(self.proxy_port)),
        ] + super().replacements 

@dataclass
class TopologyConfig:
    """
    A complete description of the environment used for the experiment(s)
    :param str config_file: Path (relative to module root) containing the config to use
    """
    def __init__(self, file_path):
        with open(os.path.join(ROOT_DIR, file_path), "r") as fin:
            config = yaml.safe_load(fin)
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

    def __str__(self):
        nodes_str = ""
        for node in self.nodes:
            nodes_str += f"\n  {node}"
        return \
            f"Nodes: {nodes_str}\n" + \
            f"Proxy: {self.proxy}\n"

if __name__ == "__main__":
    topology = TopologyConfig("config/topology.example.yml")