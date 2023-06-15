# Weird to support pre and post 3.8
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from typing import Union, NamedTuple
from datetime import datetime

### PATRONI EVENTS ###
# Old leader events
POL_EventType = Literal[
    "failover_received",
    "candidate_ping",
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
    "first_lead",
]

EventType = Union[POL_EventType, PNL_EventType]

class Event(NamedTuple):
    event: EventType
    marker: str
    timestamp: datetime

def Event2Dict(event: Event) -> "dict[str, Union[str, datetime]]":
    return {
        "event": event.event,
        "timestamp": event.timestamp
    }

class POLFailoverReceived(Event):
    event = "failover_received"
    marker = "received failover request"

class POLCandidatePing(Event):
    event = "candidate_ping"
    marker = "Got response from"

class POLDemoteSelf(Event):
    event = "demote_self"
    marker = "Demoting self (graceful)"

class POLKeyReleased(Event):
    event = "key_released"
    marker = "key released"

class POLClosePGConn(Event):
    event = "close_pg_conn"
    marker = "closed patroni connection to the postgresql cluster"

class POLAcceptingConns(Event):
    event = "accepting_conns"
    marker = "accepting connections"

class POLEstablishingNewConn(Event):
    event = "establishing_new_conn"
    marker = "establishing a new patroni connection to the postgres cluster"

POLEvent = Union[
    POLFailoverReceived,
    POLCandidatePing,
    POLCandidatePing,
    POLDemoteSelf,
    POLKeyReleased,
    POLClosePGConn,
    # POLAcceptingConns,
    POLEstablishingNewConn
]
POLOrder = [
    POLFailoverReceived,
    POLCandidatePing,
    POLCandidatePing,
    POLDemoteSelf,
    POLKeyReleased,
    POLClosePGConn,
    # POLAcceptingConns,
    POLEstablishingNewConn
]

class PNLLastFollow(Event):
    event = "last_follow"
    marker = "a secondary, and following a leader"

class PNLWritingKeyToService(Event):
    event = "writing_key_to_service"
    marker = "to key /service/patroni-experiments/leader"

class PNLCleanUp(Event):
    event = "clean_up"
    marker = "Cleaning up failover key after acquiring leader lock"

class PNLPromoteSelf(Event):
    event = "promote_self"
    marker = "promoted self to leader by acquiring session lock"

class PNLClearRewindState(Event):
    event = "clear_rewind"
    marker = "cleared rewind state after becoming the leader"

class PNLFirstLead(Event):
    event = "first_lead"
    marker = "the leader with the lock"

PNLEvent = Union[
    PNLLastFollow,
    PNLWritingKeyToService,
    PNLCleanUp,
    PNLPromoteSelf,
    PNLClearRewindState,
    PNLFirstLead,
]
PNLOrder = [
    PNLLastFollow,
    PNLWritingKeyToService,
    PNLCleanUp,
    PNLPromoteSelf,
    PNLClearRewindState,
    PNLFirstLead,
]
