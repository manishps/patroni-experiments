from events import Event, POLEvent, POLOrder, PNLEvent, PNLOrder
from io import TextIOWrapper
from typing import List
from datetime import datetime
import copy

def scrape_POL_events(fin: TextIOWrapper) -> List[POLEvent]:
    result = []
    eix = 0
    for line in fin.readlines():
        if eix >= len(POLOrder):
            break
        marker = POLOrder[eix].marker
        if marker in line:
            event = copy.deepcopy(POLOrder[eix])
            event.timestamp = datetime.strptime(line[:23] + "000", "%Y-%m-%d %H:%M:%S,%f")
            result.append(event)
            eix += 1
    return result

def scrape_PNL_events(fin: TextIOWrapper) -> List[PNLEvent]:
    result = []
    last_follow_ix = -1
    # First get the ix of the last follow
    follow = PNLOrder[0]
    for ix, line in enumerate(fin.readlines()):
        if follow.marker in line:
            last_follow_ix = ix
    # Then we can just speedrun sequential
    eix = 0
    for ix, line in enumerate(fin.readlines()):
        print(line)
        if ix < last_follow_ix:
            continue
        if eix >= len(PNLOrder):
            break
        marker = PNLOrder[eix].marker
        if marker in line:
            event = copy.deepcopy(PNLOrder[eix])
            event.timestamp = datetime.strptime(line[:23] + "000", "%Y-%m-%d %H:%M:%S,%f")
            result.append(event)
            eix += 1
    return result
        
    

if __name__ == "__main__":
    with open("../patroni/logs/patroni.log", "r") as fin:
        print(scrape_PNL_events(fin))