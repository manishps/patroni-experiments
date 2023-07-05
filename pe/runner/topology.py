import os
import jsonpickle
from tqdm import tqdm
from pe.config.parse import TopologyConfig
from pe.runner.agent import Agent, Node, Proxy
import time


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
        self.is_local = is_local
    
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

    def boot(self, verbose=True):
        """
        Start up every node in the topology
        """
        if self.is_local:
            if verbose:
                print("Cleaning up local instances...")
            # Kill any etcd/patroni servers
            os.system('pkill -9 etcd')
            os.system('pkill -9 -f "bin/patroni"')

        if verbose:
            print("Booting topology...")
        for agent in tqdm(self.agents, disable=not verbose):
            agent.boot(topology=self.config)
    
    def stop(self, verbose=True):
        """
        Stop every node in the topoloty
        """
        if verbose:
            print("Stopping topology...")
        for agent in tqdm(self.agents, disable=not verbose):
            agent.stop()


if __name__ == "__main__":
    top = Topology("config/topology.local.yml", is_local=True)
    top.boot()
    time.sleep(6)
    top.stop()
