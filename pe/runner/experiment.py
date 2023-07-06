import os
import time
import shutil
from tqdm import tqdm
from pe.runner.topology import Topology
from pe.data_generator.data_generator import DataGenerator
from pe.utils import ROOT_DIR

class Experiment():
    """
    A class to manage the experiment
    """
    def __init__(self, config_file: str, is_local: bool):
        self.config_file = config_file
        self.is_local = is_local
        self.topology = Topology(self.config_file, is_local=self.is_local)
    
    def clear_data(self):
        shutil.rmtree(f"{ROOT_DIR}/data", ignore_errors=True)
        os.mkdir(f"{ROOT_DIR}/data")
        os.mkdir(f"{ROOT_DIR}/data/etcd")
        os.mkdir(f"{ROOT_DIR}/data/patroni")
        os.mkdir(f"{ROOT_DIR}/data/postgres")
    
    def run(self) -> tuple[str, str]:
        """
        Runs the experiment and returns the name of the old and new leader
        :return tuple[str, str]: representing (old_leader_name, new_leader_name)
        """
        self.clear_data()
        self.topology.boot(verbose=True)

        print("Waiting for leadership...")
        old_leader, _ = self.topology.nodes[0].get_roles()
        old_leader_node = [node for node in self.topology.nodes if node.config.name == old_leader][0]

        print("Writing to DB...")
        dg = DataGenerator(
            self.topology.config.proxy.host,
            self.topology.config.proxy.proxy_port
        )
        dg.reset()
        dg.start_writing()
        for _ in tqdm(range(5)):
            time.sleep(1)
        
        for node in self.topology.nodes:
            node.api.ping()

        print("Issuing failover...")
        _, replicas = old_leader_node.get_roles()
        new_leader = replicas[0]
        old_leader_node.failover(new_leader)

        for node in self.topology.nodes:
            node.api.ping()

        print("Writing some more...")
        dg.write_for_x_seconds_then_stop(5)

        for node in self.topology.nodes:
            node.api.ping()

        print("Done writing")
        self.topology.stop()

        return (old_leader, new_leader)
        
    

if __name__ == "__main__":
    experiment = Experiment("config/topology.local.yml", is_local=True)
    print(experiment.run())
