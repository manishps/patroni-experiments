import sys

sys.path.append("..")

import time
from failover_manager.failover_manager import FailoverManager
from data_generator.data_generator import DataGenerator

class Runner:
    """
    A class responsible for coordinating the data generator and the
    failover manager to generate results for patroni experiments
    """
    def __init__(self):
        self.dg = DataGenerator(freq=0.2, rate=0.5)
        self.dg.reset()
        self.fm = FailoverManager()
    
    def run(self):
        """
        Actually runs the experiment
        """
        print("Writing to DB...")
        self.dg.start_writing()
        time.sleep(1)
        print("Issuing failover...")
        self.fm.issue_failover()
        self.fm.block_until_back()
        print("Recovered")
        self.dg.write_for_x_seconds_then_stop(1)

if __name__ == "__main__":
    runner = Runner()
    runner.run()