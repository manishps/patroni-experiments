import abc
import os
from pe.runner.api import Api
from pe.utils import ROOT_DIR
from typing import NamedTuple
from datetime import datetime

class Event(NamedTuple):
    timestamp: datetime
    raw: str
    readable: str

class LogScraper(abc.ABC):
    """
    A base class that represents a log scraper.
    :param str path: A path (from the root of this module) to the log to scrape
    """
    def __init__(self, path: str):
        self.path = path
        split = path.split(".")
        self.local_path = split[0] + "-local" + "." + split[1]
    
    def recreate_locally(self, api: Api):
        """
        A method that will fetch the log from the remote source (api) and recreate it
        at the same path locally for analysis.
        :param Api api: An api object bound to the machine containing the log in question
        """
        with open(os.path.join(ROOT_DIR, self.local_path), "w") as fout:
            fout.write(api.fetch_file(self.path))

    @abc.abstractclassmethod
    def get_translations(self) -> list[tuple[str, str]]:
        """
        Returns the list of markers and their translations
        """
        raise NotImplementedError("Can't get abstract translations")

    @abc.abstractclassmethod
    def scrape(self) -> list[Event]:
        """
        Does the work of scraping and returns the events in a human (and plot) friendly format
        """
        raise NotImplementedError("Can't scrape abstract translations")

class PatroniScraper(LogScraper):
    """"
    A class for scraping Patroni logs
    :param bool old: Do these logs correspond to the logs of the old leader?
    """
    def __init__(self, path: str, old: bool):
        super().__init__(path)
        self.old = old

    def get_translations(self):
        if self.old:
            return [
                ("received failover request", "Failover request received"),
                ("Got response from", "Pinging next leader"),
                ("Demoting self", "Demoting self"),
                ("key released", "Releasing DCS key"),
                ("closed patroni connection to the postgresql cluster", "Closing PG connection"),
                ("accepting connections", "Accepting new PG connections"),
                ("establishing a new patroni connection to the postgres cluster", "Establishing new PG connections"),
            ]
        else:
            return [
                ("a secondary, and following a leader", "Last heartbeat as follower"),
                ("to key /service/patroni-experiments/leader", "Claiming leader in DCS"),
                ("Cleaning up failover key after acquiring leader lock", "Cleaning up DCS"),
                ("promoted self to leader by acquiring session lock", "Promoting self"),
                ("cleared rewind state after becoming the leader", "Clearing rewind state"),
                ("the leader with the lock", "First heartbeat as leader"),
            ]
    
    def scrape(self):
        result = []
        with open(self.local_path) as fin:
            lines = fin.readlines()
        for line in lines:
            for (marker, readable) in self.get_translations():
                if marker in line:
                    raw_stamp = line[:23]
                    timestamp = datetime.strptime(raw_stamp, '%Y-%m-%d %H:%M:%S,%f')
                    result.append(Event(
                        timestamp=timestamp,
                        raw=line,
                        readable=readable
                    ))
        return result


class PostgresScraper(LogScraper):
    """"
    A class for scraping Patroni logs
    :param bool old: Do these logs correspond to the logs of the old leader?
    """
    def __init__(self, path: str, old:bool):
        if not os.path.exists(path):
            os.mkdir(path)
        self.path = path
        self.local_path = os.path.join(path, "pg-local.log")
        self.old = old
    
    def recreate_locally(self, api: Api):
        with open(os.path.join(ROOT_DIR, self.local_path), "w") as fout:
            fout.write(api.fetch_folder(self.path))

    def get_translations(self):
        if self.old:
            return [
                ("database system is ready to accept connections", "DB ready for writes"),
                ("received fast shutdown request", "DB received shutdown"),
                ("database system is shut down", "DB finished shutdown"),
                ("starting PostgreSQL", "DB restarting"),
                ("database system is ready to accept read-only connections", "DB ready for reads"),
            ]
        else:
            return [
                ("entering standby mode", "DB entering standby mode"),
                ("database system is ready to accept read-only connections", "DB ready for reads"),
                ("replication terminated by primary server", "DB replication terminated"),
                ("received promote request", "DB received promote request"),
                ("selected new timeline ID", "Starging new DB timeline"),
                ("database system is ready to accept connections", "DB ready for writes"),
            ]

    def scrape(self):
        result = []
        with open(self.local_path) as fin:
            lines = fin.readlines()
        for line in lines:
            for (marker, readable) in self.get_translations():
                if marker in line:
                    raw_stamp = line[:23]
                    timestamp = datetime.strptime(raw_stamp, '%Y-%m-%d %H:%M:%S.%f')
                    result.append(Event(
                        timestamp=timestamp,
                        raw=line,
                        readable=readable
                    ))
        return result


if __name__ == "__main__":
    ls1 = PatroniScraper("data/patroni/pe1/patroni.log", old=True)
    ls2 = PatroniScraper("data/patroni/pe2/patroni.log", old=False)
    ls3 = PostgresScraper("data/postgres/pe1/logs", old=True)
    ls4 = PostgresScraper("data/postgres/pe2/logs", old=False)

    api = Api("127.0.0.1", 3000)
    ls1.recreate_locally(api)
    ls2.recreate_locally(api)
    ls3.recreate_locally(api)
    ls4.recreate_locally(api)

    print(ls1.scrape())
    print(ls2.scrape())
    print(ls3.scrape())
    print(ls4.scrape())
