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

if __name__ == "__main__":
    with open("../patroni/logs/patroni.log", "r") as fin:
        print(scrape_POL_events(fin))