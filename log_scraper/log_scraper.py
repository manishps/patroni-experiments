# Weird to support pre and post 3.8
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from typing import Union

### PATRONI EVENTS ###
# Old leader events
POL_EventType = Literal[
    "failover_received",
    "candidate_ping1",
    "candidate_ping2",
    "demote_self",
    "key_released",
    "close_pg_conn",
    "accepting_conns",
    "establishing_new_conn"
]
# New leader events
PNL_EventType = Literal[
    "last_follow",
    "writing_key_to_service",
    "clean_up",
    "promote_self",
    "clear_rewind",
    "first_read",
]

EventType = Union[POL_EventType, PNL_EventType]

class Event:
    """
    Class for organizing meta-data about stuff that happens in the log
    """
    def __init__(self):
        self.type: EventType = "failover_received"
        


class LogScraper:
    """
    A class to scrape the logs (from Patroni, etcd, etc) and return
    the timestamps of certain events
    """

