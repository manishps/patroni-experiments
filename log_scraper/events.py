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

### POSTGRES EVENTS ###
# Old leader events
GOL_EventType = Literal[
    "ready_for_writes",
    "shutdown_received",
    "shutdown_complete",
    "restarting",
    "ready_for_reads",
]
# New leader events
GNL_EventType = Literal[
    "entering_standby_mode",
    "ready_for_reads",
    "replication_terminated",
    "promote_received",
    "new_timeline",
    "ready_for_writes"
]

# Common event stuff

EventType = Union[POL_EventType, PNL_EventType, GOL_EventType, GNL_EventType]

class Event(NamedTuple):
    event: EventType
    source: Literal["patroni", "postgres"]
    timestamp: str
    readable: str
    marker: str

def Event2Dict(event: Event) -> "dict[str, Union[str, datetime]]":
    return {
        "event": event.event,
        #"source": event.source,
        "timestamp": event.timestamp,
        #"readable": event.readable
    }

# Patroni event classes

class PatroniEvent(Event):
    source = "patroni"

class POLFailoverReceived(PatroniEvent):
    event = "failover_received"
    marker = "received failover request"

class POLCandidatePing(PatroniEvent):
    event = "candidate_ping"
    marker = "Got response from"

class POLDemoteSelf(PatroniEvent):
    event = "demote_self"
    marker = "Demoting self (graceful)"

class POLKeyReleased(PatroniEvent):
    event = "key_released"
    marker = "key released"

class POLClosePGConn(PatroniEvent):
    event = "close_pg_conn"
    marker = "closed patroni connection to the postgresql cluster"

class POLAcceptingConns(PatroniEvent):
    event = "accepting_conns"
    marker = "accepting connections"

class POLEstablishingNewConn(PatroniEvent):
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

class PNLLastFollow(PatroniEvent):
    event = "last_follow"
    marker = "a secondary, and following a leader"

class PNLWritingKeyToService(PatroniEvent):
    event = "writing_key_to_service"
    marker = "to key /service/patroni-experiments/leader"

class PNLCleanUp(PatroniEvent):
    event = "clean_up"
    marker = "Cleaning up failover key after acquiring leader lock"

class PNLPromoteSelf(PatroniEvent):
    event = "promote_self"
    marker = "promoted self to leader by acquiring session lock"

class PNLClearRewindState(PatroniEvent):
    event = "clear_rewind"
    marker = "cleared rewind state after becoming the leader"

class PNLFirstLead(PatroniEvent):
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

# Postgres event classes

class PostgresEvent(Event):
    source = "postgres"

class GOLReadyForWrites(PostgresEvent):
    event = "ready_for_writes"
    marker = "database system is ready to accept connections"

class GOLShutdownReceived(PostgresEvent):
    event = "shutdown_received"
    marker = "received fast shutdown request"

class GOLShutdownComplete(PostgresEvent):
    event = "shutdown_complete"
    marker = "database system is shut down"

class GOLRestarting(PostgresEvent):
    event = "restarting"
    marker = "starting PostgreSQL"

class GOLReadyForReads(PostgresEvent):
    event = "ready_for_reads"
    marker = "database system is ready to accept read-only connections"

GOLEvent = Union[
    GOLReadyForWrites,
    GOLShutdownReceived,
    GOLShutdownComplete,
    GOLRestarting,
    GOLReadyForReads,
]
GOLOrder = [
    GOLReadyForWrites,
    GOLShutdownReceived,
    GOLShutdownComplete,
    GOLRestarting,
    GOLReadyForReads,
]

class GNLEnteringStandby(PostgresEvent):
    event = "entering_standby_mode"
    marker = "entering standby mode"

class GNLReadyForReads(PostgresEvent):
    event = "ready_for_reads"
    marker = "database system is ready to accept read-only connections"

class GNLReplicationTerminated(PostgresEvent):
    event = "replication_terminated"
    marker = "replication terminated by primary server"

class GNLPromoteReceived(PostgresEvent):
    event = "promote_received"
    marker = "received promote request"

class GNLNewTimeline(PostgresEvent):
    event = "new_timeline"
    marker = "selected new timeline ID"

class GNLReadyForWrites(PostgresEvent):
    event = "ready_for_writes"
    marker = "database system is ready to accept connections"

GNLEvent = Union[
    GNLEnteringStandby,
    GNLReadyForReads,
    GNLPromoteReceived,
    GNLNewTimeline,
    GNLReadyForWrites
]
GNLOrder = [
    GNLEnteringStandby,
    GNLReadyForReads,
    GNLPromoteReceived,
    GNLNewTimeline,
    GNLReadyForWrites
]