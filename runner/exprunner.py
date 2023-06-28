import sys
import os

sys.path.append("..")

import time
from failover_manager.failover_manager import FailoverManager
from data_generator.data_generator import DataGenerator
import requests
import pdb

class Runner:
    """
    A class responsible for coordinating the data generator and the
    failover manager to generate results for patroni experiments
    """
    def __init__(self, viewer=False):
        # Load the addresses of the machines
        with open ("../.config/.HOST_1", "r") as fin:
            self.host1 = fin.readline()
        with open ("../.config/.HOST_2", "r") as fin:
            self.host2 = fin.readline()
        with open ("../.config/.HOST_3", "r") as fin:
            self.host3 = fin.readline()
        with open ("../.config/.HOST_4", "r") as fin:
            self.host4 = fin.readline()
        # Failover manager, useful to check leader status during setup
        # (hence declared here, unlike the data generator)
        self.fm = FailoverManager()
        # Results
        self.POL_events = []
        self.PNL_events = []
        if not viewer:
            self.graceful, self.ttl, self.exp_name = self.solicit_experiment()
            self.out_dir = os.path.join("runs", self.exp_name)
            if os.path.exists(self.out_dir):
                os.system(f"rm -rf {self.out_dir}")
            os.system(f"mkdir {self.out_dir}")
    
    def solicit_experiment(self) -> tuple[bool, int, str]:
        """
        Gets input from the user about the experiment.
        :return: (graceful Y/N, ttl, name)
        """
        graceful = input("Failover gracefully? (y/n): ").lower() == "y"
        ttl = int(input("DCS time to live (ttl): "))
        exp_name = input("Experiment name: ")
        return (graceful, ttl, exp_name)
    
    def issue_command(self, host: str, comm: str):
        """
        Helper function to make the request
        """
        requests.post(f"http://{host}:3000/exec_command/{comm}")
    
    def stop_node(self, host: str):
        """
        Helper function to stop etcd and patroni on a node
        """
        self.issue_command(host, "pkill patroni")
        self.issue_command(host, "pkill etcd")

    def reset_node(self, host: str):
        """
        Connect to the node_server running at the given host and kill etcd
        and patroni. Then clear the patroni logs, wait a second, and reboot
        all the processes
        """
        self.stop_node(host)
        self.issue_command(host, "rm patroni/logs/patroni.log")
        time.sleep(1.0) # Give process time to die and free ports
    
    def reset_nodes(self, clear_data = True):
        """
        Helper function to reset the nodes, hopefully in order, so that
        pe1 is first leader
        """
        print("Resetting nodes...")
        for host in [self.host1, self.host2, self.host3]:
            self.reset_node(host)
        
        # Start etcd on all the nodes
        for host in [self.host1, self.host2, self.host3]:
            if clear_data:
                self.issue_command(host, "make reset-data")
            self.issue_command(host, "make node-etcd&")
        
        # Start patroni only on node 1 and wait for it to claim leader
        self.issue_command(self.host1, "make node-patroni&")
        time.sleep(3)
        self.fm.block_until_back(self.host1)

        # Now we can start patroni on other nodes, and know that they will be replicas
        for host in [self.host2, self.host3]:
            self.issue_command(host, "make node-patroni&")

        time.sleep(3)
    
    def stop_proxy(self):
        """
        Helper function to stop the proxy
        """
        self.issue_command(self.host4, "pkill proxy")

    def reset_proxy(self):
        """
        Helper function to reset the proxy
        """
        print("Resetting proxy...")
        self.stop_proxy()
        time.sleep(1.0)
        self.issue_command(self.host4, "make proxy&")

    def reset(self, clear_data = True):
        """
        Resets the nodes and the proxy
        """
        self.reset_nodes(clear_data=clear_data)
        self.reset_proxy()
    
    def do_work(self):
        """
        Actually runs the experiment
        """
        print("Connecting to DB")
        # The interactive experiment tools
        self.dg = DataGenerator(freq=0.3, rate=0.5)
        self.dg.reset()
        print("Writing to DB...")
        self.dg.start_writing()
        time.sleep(10)
        print("Issuing failover...")
        self.fm.issue_failover(
            graceful=self.graceful,
            issue_command=lambda c: self.issue_command(self.host1, c)
        )
        self.fm.block_until_back(self.host2)
        print("Status up...")
        self.dg.write_for_x_seconds_then_stop(10)
        print("Recovered + written")

    def stop(self):
        # Stop everything
        for host in [self.host1, self.host2, self.host3]:
            self.stop_node(host)
        self.stop_proxy()
    
    def collect_logs(self):
        """
        Collects the log events from the nodes
        """
        print("Collecting logs...")

        self.stop()

        # Patroni Old Leader (POL)
        resp = requests.get(f"http://{self.host1}:3000/get_logs/POL")
        self.POL_events = resp.json()["data"]
        with open(os.path.join(self.out_dir, "POL_data.json"), "w") as fout:
            fout.write(resp.text)

        # Patroni New Leader (PNL)
        resp = requests.get(f"http://{self.host2}:3000/get_logs/PNL")
        self.POL_events = resp.json()["data"]
        with open(os.path.join(self.out_dir, "PNL_data.json"), "w") as fout:
            fout.write(resp.text)
        
        # Postgres Old Leader (GOL)
        resp = requests.get(f"http://{self.host1}:3000/get_logs/GOL")
        self.GOL_events = resp.json()["data"]
        with open(os.path.join(self.out_dir, "GOL_data.json"), "w") as fout:
            fout.write(resp.text)
        
        # Postgres New Leader (GNL)
        resp = requests.get(f"http://{self.host2}:3000/get_logs/GNL")
        self.GOL_events = resp.json()["data"]
        with open(os.path.join(self.out_dir, "GNL_data.json"), "w") as fout:
            fout.write(resp.text)

    def run(self):
        # pdb.set_trace()
        self.reset()
        self.do_work()
        self.collect_logs()

if __name__ == "__main__":
    runner = Runner()
    runner.run()