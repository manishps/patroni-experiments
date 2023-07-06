import time
import os
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
        os.system(f"rm -rf {ROOT_DIR}/../data")
        os.system(f"mkdir {ROOT_DIR}/../data")
        os.system(f"mkdir {ROOT_DIR}/../data/etcd")
        os.system(f"mkdir {ROOT_DIR}/../data/patroni")
        os.system(f"mkdir {ROOT_DIR}/../data/postgres")
    
    def run(self):
        self.clear_data()
        self.topology.boot(verbose=True)
        print("Writing to DB...")
        self.dg = DataGenerator(
            self.topology.config.proxy.host,
            self.topology.config.proxy.proxy_port
        )
        self.dg.reset()
        self.dg.write_for_x_seconds_then_stop(10)
        time.sleep(10)
        print("Done writing")
        self.topology.stop()
        
    

if __name__ == "__main__":
    experiment = Experiment("config/topology.local.yml", is_local=True)
    experiment.run()
