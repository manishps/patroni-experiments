import os
import subprocess
import time
import yaml
import requests
from configparser import ConfigParser
from pe.config.parse import AgentConfig, NodeConfig, ProxyConfig, TopologyConfig
from pe.exceptions import BootError
from pe.runner.api import Api
from pe.utils import kill_process_on_port, ROOT_DIR, replace_strs

class Agent():
    """
    An active agent in the experiment
    :param AgentConfig config: The configuration for this agent
    :param bool is_local: Is this agent running locally?
    """
    def __init__(self, config: AgentConfig, is_local: bool):
        self.api = Api(config.host, config.api_port)
        self.config = config
        self.is_local = is_local

    def boot(self, topology: TopologyConfig):
        if self.is_local:
            # If this agent is local, restart the Flask server locally
            kill_process_on_port(self.api.port)
            subprocess.Popen([
                "python3",
                os.path.join(ROOT_DIR, "runner", "api.py"),
                self.api.host,
                str(self.api.port)
            ])#, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Ensure the flask server is up
        MAX_RETRIES = 10
        DELAY = 0.5
        for _ in range(MAX_RETRIES):
            try:
                self.api.ping() 
                break
            except:
                time.sleep(DELAY)
        else:
            raise BootError(f"{self.config.name} api is not ready after {MAX_RETRIES * DELAY} seconds")
    
    def stop(self):
        raise NotImplementedError("The method to stop nodes should be implemented specifically")

class Node(Agent):
    """
    An active NODE in the experiment
    :param NodeConfig config: The configuration for this node
    :param bool is_local: Is this node running locally?
    """
    def __init__(self, config: NodeConfig, is_local: bool):
        self.api = Api(config.host, config.api_port)
        self.config = config
        self.is_local = is_local
    
    def construct_patroni_config(self):
        """
        Constructs the patroni configuration by looking at node config
        and the template
        NOTE: Unlike previous version, the patroni config gets sent over
        the wire to the node, so it's easier to play with on the fly
        """
        with open(os.path.join(ROOT_DIR, "config", "patroni.yml"), "r") as fin:
            config = yaml.safe_load(fin)
        
        for dir in ["postgres", "patroni"]:
            path = os.path.join(ROOT_DIR, "data", dir)
            if not os.path.exists(path + "/" + self.config.name):
                os.mkdir(path + "/" + self.config.name, mode=0o750)

        replacements = self.config.replacements + [
            ("pg_data_dir", f"{ROOT_DIR}/data/postgres/{self.config.name}"),
            ("patroni_log_dir", f"{ROOT_DIR}/data/patroni/{self.config.name}")
        ]
        
        return replace_strs(config, replacements)
    
    def boot(self, topology: TopologyConfig):
        """
        Start a node (etcd, patroni)
        """
        super().boot(topology) # This ensures that the Flask server is up
        self.api.start_etcd(self.config.name, topology)
        patroni_dict = self.construct_patroni_config()
        self.api.start_patroni(patroni_dict)
    
    def stop(self):
        """
        Stop a node (patroni, etcd)
        """
        self.api.stop_patroni()
        self.api.stop_etcd()
    
    def get_roles(self, block=True) -> tuple[str, list[str]]:
        """
        Uses this nodes patroni api to get the name of the current leader
        and name of the followers
        :param bool block: If the initial request fails, should we retry till success?
        """
        while True:
            try:
                resp = requests.get(f"http://{self.config.host}:{self.config.patroni_port}/cluster")
                data = resp.json()
                primary = ""
                replicas = []
                for member in data["members"]:
                    if member["role"] == "leader":
                        primary = member["name"]
                    else:
                        replicas.append(member["name"])
                if len(primary) == 0:
                    raise ValueError("No primary")
                return (primary, replicas)
            except Exception as e:
                if not block:
                    raise e
                else:
                    time.sleep(0.1)
    
    def failover(self, new_leader: str):
        """
        Triggers a failover. Note that if this node is not the leader
        it will fail.
        :param str new_leader: Who to fail over to
        """
        resp = requests.post(f"http://{self.config.host}:{self.config.patroni_port}/failover", json={
            "candidate": new_leader
        })
        

class Proxy(Agent):
    """
    The PROXY in use for the experiment
    :param NodeConfig config: The configuration for this node
    :param bool is_local: Is this node running locally?
    """
    def __init__(self, config: ProxyConfig, is_local: bool):
        self.api = Api(config.host, config.api_port)
        self.config = config
        self.is_local = is_local 
    
    def boot(self, topology: TopologyConfig):
        """
        Start the proxy
        """
        super().boot(topology) # This ensures that the Flask server is up
        with open(os.path.join(ROOT_DIR, "config", "haproxy.cfg"), "r") as fin:
            raw_conf = fin.read()
        
        replacements = self.config.replacements + [
            ("server_lines","\n    ".join([
                f"server {node.name} {node.host}:{node.pg_port} maxconn 100 check port {node.patroni_port}" for node in topology.nodes
            ]))
        ]
        conf = replace_strs({"data": raw_conf}, replacements)["data"]

        self.api.start_proxy(conf)

    def stop(self):
        self.api.stop_proxy()
