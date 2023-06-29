import os
import subprocess
from pe.config.parse import AgentConfig, TopologyConfig
from pe.runner.api import Api
from pe.utils import kill_process_on_port, ROOT_DIR

class Agent():
    """
    An active agent in the experiment
    :param AgentConfig config: The configuration for this agent
    :param bool is_local: Is this agent running locally?
    """
    def __init__(self, config: AgentConfig, is_local: bool):
        self.config = config
        self.api = Api(config.host, config.api_port)
        self.is_local = is_local

    def boot(self):
        if self.is_local:
            # If this agent is local, restart the Flask server locally
            kill_process_on_port(self.api.port)
            subprocess.Popen([
                "python3",
                os.path.join(ROOT_DIR, "runner", "api.py"),
                self.api.host,
                str(self.api.port)
            ])

class Node(Agent):
    pass

class Proxy(Agent):
    pass

if __name__ == "__main__":
    top = TopologyConfig("config/topology.local.yml")
    agent = Agent(top.me, is_local=True)
    agent.boot()
    print("Success! Flask server booted in another process")
    