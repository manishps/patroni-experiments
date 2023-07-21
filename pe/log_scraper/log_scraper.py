import abc
import os
from datetime import datetime
from typing import NamedTuple, Union
from pe.runner.api import Api


class Event(NamedTuple):
    """
    Represents an observable event from the logs that we want to plot
    """

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
        with open(os.path.join(self.local_path), "w") as fout:
            fout.write(api.fetch_file(self.path))

    @classmethod
    def get_translations(cls) -> list[tuple[str, str]]:
        """
        Returns the list of markers and their translations
        """
        raise NotImplementedError("Can't get abstract translations")

    @classmethod
    def scrape(cls) -> list[Event]:
        """
        Does the work of scraping and returns the events in a human (and plot) friendly format
        """
        raise NotImplementedError("Can't scrape abstract translations")


class PatroniScraper(LogScraper):
    """ "
    A class for scraping Patroni logs
    :param bool old: Do these logs correspond to the logs of the old leader?
    """

    def __init__(self, path: str, old: bool):
        super().__init__(path)
        self.old = old

    def get_translations(self):
        """ """
        if self.old:
            return [
                ("received failover request", "Failover request received"),
                ("Got response from", "Pinging next leader"),
                ("Demoting self", "Demoting self"),
                ("key released", "Releasing DCS key"),
                (
                    "closed patroni connection to the postgresql cluster",
                    "Closing PG connection",
                ),
                ("accepting connections", "Accepting new PG connections"),
                # ("establishing a new patroni connection to the postgres cluster", "Establishing new PG connections"),
            ]
        else:
            return [
                ("a secondary, and following a leader", "Last heartbeat as follower"),
                # ("to key /service/patroni-experiments/leader", "Claiming leader in DCS"),
                (
                    "Cleaning up failover key after acquiring leader lock",
                    "Cleaning up DCS",
                ),
                ("promoted self to leader by acquiring session lock", "Promoting self"),
                (
                    "cleared rewind state after becoming the leader",
                    "Clearing rewind state",
                ),
                ("the leader with the lock", "First heartbeat as leader"),
            ]

    def scrape(self):
        """ """
        result = []
        with open(self.local_path) as fin:
            lines = fin.readlines()
        if self.old:
            # Old leader has simple marker -> event logic
            for line in lines:
                for marker, readable in self.get_translations():
                    if marker in line:
                        raw_stamp = line[:23]
                        timestamp = datetime.strptime(raw_stamp, "%Y-%m-%d %H:%M:%S,%f")
                        result.append(
                            Event(timestamp=timestamp, raw=line, readable=readable)
                        )
        else:
            # For the new leader, in order to accurately track the "last heartbeat as follower"
            # and the "first heartbeat as leader" we need to handle markers differently based
            # on whether the machine has been promoted
            has_promoted = False
            last_follow: Union[Event, None] = None
            first_lead: Union[Event, None] = None
            for line in lines:
                for marker, readable in self.get_translations():
                    if marker not in line:
                        continue
                    raw_stamp = line[:23]
                    timestamp = datetime.strptime(raw_stamp, "%Y-%m-%d %H:%M:%S,%f")
                    event = Event(timestamp=timestamp, raw=line, readable=readable)
                    if "and following a leader" in marker:
                        # Special logic for last follow
                        if not has_promoted:
                            last_follow = event
                    elif "the leader with the lock" in marker:
                        # Special logic for the first lead, only update right after has_promoted and first_lead
                        if has_promoted and first_lead == None:
                            first_lead = event
                    else:
                        if "promoted self to leader" in marker:
                            has_promoted = True
                        result.append(event)
            if last_follow is not None:
                result.append(last_follow)
            if first_lead is not None:
                result.append(first_lead)
            result.sort(key=lambda e: e.timestamp)
        return result


class PostgresScraper(LogScraper):
    """ "
    A class for scraping Patroni logs
    :param bool old: Do these logs correspond to the logs of the old leader?
    """

    def __init__(self, path: str, old: bool):
        if not os.path.exists(path):
            os.mkdir(path)
        self.path = path
        self.local_path = os.path.join(path, "pg-local.log")
        self.old = old

    def recreate_locally(self, api: Api):
        with open(os.path.join(self.local_path), "w") as fout:
            fout.write(api.fetch_folder(self.path))

    def get_translations(self):
        if self.old:
            return [
                # (
                #    "database system is ready to accept connections",
                #    "DB ready for writes",
                # ),
                ("received fast shutdown request", "DB received shutdown"),
                ("database system is shut down", "DB finished shutdown"),
                # ("starting PostgreSQL", "DB restarting"),
                (
                    "database system is ready to accept read-only connections",
                    "Node ready as replica. \nDB ready for reads",
                ),
            ]
        else:
            return [
                # ("entering standby mode", "DB entering standby mode"),
                # (
                #    "database system is ready to accept read-only connections",
                #    "DB ready for reads",
                # ),
                (
                    "replication terminated by primary server",
                    "DB replication terminated",
                ),
                ("received promote request", "DB received promote request"),
                ("selected new timeline ID", "Starting new DB timeline"),
                (
                    "database system is ready to accept connections",
                    "DB ready for writes",
                ),
            ]

    def scrape(self):
        result = []
        with open(self.local_path) as fin:
            lines = fin.readlines()
        if self.old:
            for line in lines:
                for marker, readable in self.get_translations():
                    if marker in line:
                        raw_stamp = line[:23]
                        timestamp = datetime.strptime(raw_stamp, "%Y-%m-%d %H:%M:%S.%f")
                        result.append(
                            Event(timestamp=timestamp, raw=line, readable=readable)
                        )
        else:
            has_started_new_timeline = False
            for line in lines:
                for marker, readable in self.get_translations():
                    if marker in line:
                        if (
                            "accept connections" in marker
                            and not has_started_new_timeline
                        ):
                            continue
                        if "selected new timeline ID" in marker:
                            has_started_new_timeline = True
                        raw_stamp = line[:23]
                        timestamp = datetime.strptime(raw_stamp, "%Y-%m-%d %H:%M:%S.%f")
                        result.append(
                            Event(timestamp=timestamp, raw=line, readable=readable)
                        )
        return result


class HAProxyScraper(LogScraper):
    """
    A class for scraping HAProxy logs for important events in the experiment
    """

    def __init__(self, path, old_name: str, new_name: str):
        super().__init__(path)
        self.old_name = old_name
        self.new_name = new_name

    def get_translations(self):
        """ """
        return [
            (
                f"Health check for server patroni-experiments/{self.old_name} failed",
                "Proxy health check on old leader failed",
            ),
            (
                f"Health check for server patroni-experiments/{self.old_name} succeeded",
                "Proxy health check on old leader succeeded",
            ),
            (
                f"Server patroni-experiments/{self.old_name} is UP",
                "Old leader marked as UP",
            ),
            (
                f"Server patroni-experiments/{self.old_name} is DOWN",
                "Old leader marked as DOWN",
            ),
            (
                f"Health check for server patroni-experiments/{self.new_name} failed",
                "Proxy health check on new leader failed",
            ),
            (
                f"Health check for server patroni-experiments/{self.new_name} succeeded",
                "Proxy health check on new leader succeeded",
            ),
            (
                f"Server patroni-experiments/{self.new_name} is UP",
                "New leader marked as UP",
            ),
            (
                f"Server patroni-experiments/{self.new_name} is DOWN",
                "New leader marked as DOWN",
            ),
        ]

    def scrape(self):
        """ """
        # NOTE: Because of a weird quirk in the HAProxy logging config, some
        # events get logged twice. One of the times they get logged, it looks
        # like <#>timestamp thing and the other is [STATUS] (####) : thing.
        # We only want to use the ones that have the timestamp, so this whole
        # scraper is written assuming that anything that doesn't start with <#>
        # will be thrown out.
        result = []
        with open(self.local_path, "r") as fin:
            lines = fin.readlines()
        for line in lines:
            if line[0] != "<":
                # Sign that this line will _not_ contain a timestamp
                continue
            for marker, readable in self.get_translations():
                if marker not in line:
                    continue
                raw_stamp = line[3:29]
                timestamp = datetime.strptime(raw_stamp, "%Y-%m-%dT%H:%M:%S.%f")
                result.append(Event(timestamp=timestamp, raw=line, readable=readable))
        return result


if __name__ == "__main__":
    ls1 = PatroniScraper("data/patroni/pe1/patroni.log", old=True)
    ls2 = PatroniScraper("data/patroni/pe2/patroni.log", old=False)
    ls3 = PostgresScraper("data/postgres/pe1/logs", old=True)
    ls4 = PostgresScraper("data/postgres/pe2/logs", old=False)
    ls5 = HAProxyScraper("data/haproxy/proxy.log", old_name="pe1", new_name="pe2")

    default_api = Api("127.0.0.1", 3000)
    ls1.recreate_locally(default_api)
    ls2.recreate_locally(default_api)
    ls3.recreate_locally(default_api)
    ls4.recreate_locally(default_api)
    ls5.recreate_locally(default_api)

    print(ls1.scrape())
    print(ls2.scrape())
    print(ls3.scrape())
    print(ls4.scrape())
    print(ls5.scrape())
