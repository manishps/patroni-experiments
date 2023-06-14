import requests

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
        self.get_leader_host()

    def get_leader_host(self) -> str:
        """
        Returns the host of the current leader
        """
        resp = requests.get(f"http://{self.host1}:8009/cluster")
        print(resp.text)
        return ""

if __name__ == "__main__":
    fm = FailoverManager()