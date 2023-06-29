from pe.config.parse import TopologyConfig
from pe.runner.agent import Agent, Node, Proxy


class Topology:
    """
    An active topology that we can run experiments on
    :param str config_path: Path (from module root) to the topology configuration file
    :param bool is_local: Is this topology running locally?
    """
    def __init__(self, config_path: str, is_local: bool):
        self.config = TopologyConfig(config_path)
        self.nodes: list[Node] = []
        for node in self.config.nodes:
            self.nodes.append(Node(node, is_local))
        self.proxy = Proxy(self.config.proxy, is_local)
    
    @property
    def agents(self) -> list[Agent]:
        """
        Get all the agents. Has to be this verbose for typing
        """
        result: list[Agent] = []
        for node in self.nodes:
            result.append(node)
        result.append(self.proxy)
        return result
    
    def boot(self):
        for agent in self.agents:
            agent.boot()


if __name__ == "__main__":
    top = Topology("config/topology.local.yml", True)
    top.boot()
