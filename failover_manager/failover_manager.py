from typing import NamedTuple
import requests
import random
import time

class Node(NamedTuple):
    name: str
    host: str
    port: int

class FailoverManager:
    """
    A class that wraps a precise failover command and records data
    about the failover we'll need for analysis
    """
    def __init__(self):
        with open ("../.config/.HOST_1", "r") as fin:
            self.host1 = fin.readline()
        with open ("../.config/.HOST_2", "r") as fin:
            self.host2 = fin.readline()
        with open ("../.config/.HOST_3", "r") as fin:
            self.host3 = fin.readline()
        with open ("../.config/.HOST_4", "r") as fin:
            self.host4 = fin.readline()

    def get_nodes(self) -> tuple[Node, list[Node]]:
        """
        Returns the host of the current leader
        """
        resp = requests.get(f"http://{self.host1}:8009/cluster")
        leader = None
        replicas = []
        for member in resp.json()["members"]:
            node = Node(
                name=member["name"],
                host=member["host"],
                port=member["port"]
            )
            if member["role"] == "leader":
                if leader != None:
                    raise Exception("Multiple leaders")
                leader = node
            else:
                replicas.append(node)
        
        if leader == None:
            raise Exception("No leader detected (something's gone very bad, check VM logs)")
        
        return (leader, replicas)

    def issue_failover(self):
        """
        Simply gets the node hierarchy and then issues a failover to the leader, randomly
        selecting a replica to promote
        """
        leader, replicas = self.get_nodes()
        promote = random.choice(replicas)
        resp = requests.post(f"http://{leader.host}:8009/failover", json={
            "candidate": promote.name
        })
        if resp.status_code != 200:
            raise Exception("Failover failed")
    
    def block_until_back(self):
        """
        A function that will block until it's able to successfully query cluster
        information that includes a leader
        """
        MAX_TRIES = 100
        DELAY = 0.1
        for _ in range(MAX_TRIES):
            try:
                leader, _ = self.get_nodes()
                if leader != None:
                    break
            finally:
                pass
            time.sleep(DELAY)



if __name__ == "__main__":
    fm = FailoverManager()
    fm.issue_failover()
    fm.block_until_back()

    