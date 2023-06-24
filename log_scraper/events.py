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
        "source": event.source,
        "timestamp": event.timestamp,
        "readable": event.readable
    }

# Patroni event classes

class PatroniEvent(Event):
    source = "patroni"

class POLFailoverReceived(PatroniEvent):
    event = "failover_received"
    marker = "received failover request"
    readable = "Failover request received"

class POLCandidatePing(PatroniEvent):
    event = "candidate_ping"
    marker = "Got response from"
    readable = "Pinging next leader"

class POLDemoteSelf(PatroniEvent):
    event = "demote_self"
    marker = "Demoting self (graceful)"
    readable = "Demoting self"

class POLKeyReleased(PatroniEvent):
    event = "key_released"
    marker = "key released"
    readable = "Releasing DCS key"

class POLClosePGConn(PatroniEvent):
    event = "close_pg_conn"
    marker = "closed patroni connection to the postgresql cluster"
    readable = "Closing PG connection"

class POLAcceptingConns(PatroniEvent):
    event = "accepting_conns"
    marker = "accepting connections"
    readable = "Accepting new PG connections"

class POLEstablishingNewConn(PatroniEvent):
    event = "establishing_new_conn"
    marker = "establishing a new patroni connection to the postgres cluster"
    readable = "Establishing new PG connections"

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
    readable = "Last heartbeat as follower"

class PNLWritingKeyToService(PatroniEvent):
    event = "writing_key_to_service"
    marker = "to key /service/patroni-experiments/leader"
    readable = "Claiming leader in DCS"

class PNLCleanUp(PatroniEvent):
    event = "clean_up"
    marker = "Cleaning up failover key after acquiring leader lock"
    readable = "Cleaning up DCS"

class PNLPromoteSelf(PatroniEvent):
    event = "promote_self"
    marker = "promoted self to leader by acquiring session lock"
    readable = "Promoting self"

class PNLClearRewindState(PatroniEvent):
    event = "clear_rewind"
    marker = "cleared rewind state after becoming the leader"
    readable = "Clearing rewind state"

class PNLFirstLead(PatroniEvent):
    event = "first_lead"
    marker = "the leader with the lock"
    readable = "First heartbeat as leader"

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
    readable = "DB ready for writes"

class GOLShutdownReceived(PostgresEvent):
    event = "shutdown_received"
    marker = "received fast shutdown request"
    readable = "DB received shutdown"

class GOLShutdownComplete(PostgresEvent):
    event = "shutdown_complete"
    marker = "database system is shut down"
    readable = "DB finished shutdown"

class GOLRestarting(PostgresEvent):
    event = "restarting"
    marker = "starting PostgreSQL"
    readable = "DB restarting"

class GOLReadyForReads(PostgresEvent):
    event = "ready_for_reads"
    marker = "database system is ready to accept read-only connections"
    readable = "DB ready for reads"

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
    readable = "DB entering standby mode"

class GNLReadyForReads(PostgresEvent):
    event = "ready_for_reads"
    marker = "database system is ready to accept read-only connections"
    readable = "DB ready for reads"

class GNLReplicationTerminated(PostgresEvent):
    event = "replication_terminated"
    marker = "replication terminated by primary server"
    readable = "DB replication terminated"

class GNLPromoteReceived(PostgresEvent):
    event = "promote_received"
    marker = "received promote request"
    readable = "DB received promote request"

class GNLNewTimeline(PostgresEvent):
    event = "new_timeline"
    marker = "selected new timeline ID"
    readable = "Starting new DB timeline"

class GNLReadyForWrites(PostgresEvent):
    event = "ready_for_writes"
    marker = "database system is ready to accept connections"
    readable = "DB ready for writes"

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