import os
import subprocess
import time
import yaml
from pe.config.parse import AgentConfig, NodeConfig, ProxyConfig, TopologyConfig
from pe.exceptions import BootError
from pe.runner.api import Api
from pe.utils import kill_process_on_port, ROOT_DIR

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
            ]) #, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
            path = os.path.join(ROOT_DIR, "..", "data", dir)
            if not os.path.exists(path):
                os.mkdir(path)
            if not os.path.exists(path + "/" + self.config.name):
                os.mkdir(path + "/" + self.config.name)

        def replace_strs(obj):
            """
            Helper function to recursively modify strings in a dictionary
            """
            replacements = self.config.replacements + [
                ("pg_data_dir", f"{ROOT_DIR}/../data/postgres/{self.config.name}"),
                ("patroni_log_dir", f"{ROOT_DIR}/../data/patroni/{self.config.name}")
            ]
            for key in obj:
                val = obj[key]
                if isinstance(val, str):
                    for marker, replacement in replacements:
                        val = obj[key]
                        marker = f"<{marker}>"
                        obj[key] = val.replace(marker, replacement)
                if isinstance(val, dict):
                    obj[key] = replace_strs(obj[key])
                if isinstance(val, list):
                    new_list = []
                    for item in val:
                        if not isinstance(item, str):
                            continue
                        new_str = item
                        for marker, replacement in replacements:
                            marker = f"<{marker}>"
                            new_str = new_str.replace(marker, replacement)
                        new_list.append(new_str)
                    obj[key] = new_list
            return obj
        
        return replace_strs(config)
    
    def boot(self, topology: TopologyConfig):
        super().boot(topology) # This ensures that the Flask server is up
        self.api.start_etcd(self.config.name, topology)
        patroni_dict = self.construct_patroni_config()
        self.api.start_patroni(patroni_dict)

class Proxy(Agent):
    pass
