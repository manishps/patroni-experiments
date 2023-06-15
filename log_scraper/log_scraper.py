from events import Literal, Event, POLEvent, POLOrder, PNLEvent, PNLOrder
from io import TextIOWrapper

def scrape_POL_events(fin: TextIOWrapper) -> list[POLEvent]:
    result = []
    eix = 0
    for line in fin.readlines():
        if eix >= len(POLOrder):
            break
        marker = POLOrder[eix].marker
        if marker in line:
            print(line)
            eix += 1
    return result