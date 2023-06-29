import sys

sys.path.append("..")

from pe.log_scraper.events import Event, POLEvent, POLOrder, PNLEvent, PNLOrder, \
    GOLEvent, GOLOrder, GNLEvent, GNLOrder, Event2Dict 
from io import TextIOWrapper
from typing import List
from datetime import datetime
import copy
import json

def scrape_POL_events(fin: TextIOWrapper) -> List[POLEvent]:
    result = []
    for line in fin.readlines():
        match = None
        for event in POLOrder:
            if event.marker in line:
                match = event
                break
        if match != None:
            event = copy.deepcopy(match)
            event.timestamp = line[:23]
            result.append(event)
    return result

def scrape_PNL_events(fin: TextIOWrapper) -> List[PNLEvent]:
    result = []
    last_follow_ix = -1
    # First get the ix of the last follow
    follow = PNLOrder[0]
    for ix, line in enumerate(fin.readlines()):
        if follow.marker in line:
            last_follow_ix = ix
    fin.seek(0)
    # Then we can just speedrun sequential
    for ix, line in enumerate(fin.readlines()):
        if ix < last_follow_ix:
            continue
        match = None
        for event in PNLOrder:
            if event.marker in line:
                match = event
                break
        if match != None:
            event = copy.deepcopy(match)
            event.timestamp = line[:23]
            result.append(event)
    return result

def scrape_GOL_events(fin: TextIOWrapper) -> List[GOLEvent]:
    result = []
    eix = 0
    for line in fin.readlines():
        if eix >= len(GOLOrder):
            break
        marker = GOLOrder[eix].marker
        if marker in line:
            event = copy.deepcopy(GOLOrder[eix])
            event.timestamp = line[:23]
            result.append(event)
            eix += 1
    return result

def scrape_GNL_events(fin: TextIOWrapper) -> List[GNLEvent]:
    result = []
    eix = 0
    for line in fin.readlines():
        if eix >= len(GNLOrder):
            break
        marker = GNLOrder[eix].marker
        if marker in line:
            event = copy.deepcopy(GNLOrder[eix])
            event.timestamp = line[:23]
            result.append(event)
            eix += 1
    return result
    

if __name__ == "__main__":
    with open("../patroni/logs/POL.log", "r") as fin:
        with open("../runner/POL_data.json", "w") as fout:
            raw_events = scrape_POL_events(fin)
            clean_events = {"data": [Event2Dict(e) for e in raw_events]}
            fout.write(json.dumps(clean_events))
    with open("../patroni/logs/PNL.log", "r") as fin:
        with open("../runner/PNL_data.json", "w") as fout:
            raw_events = scrape_PNL_events(fin)
            clean_events = {"data": [Event2Dict(e) for e in raw_events]}
            fout.write(json.dumps(clean_events))
    with open("../patroni/data/GOL/log/GOL.log", "r") as fin:
        with open("../runner/GOL_data.json", "w") as fout:
            raw_events = scrape_GOL_events(fin)
            clean_events = {"data": [Event2Dict(e) for e in raw_events]}
            fout.write(json.dumps(clean_events))
    with open("../patroni/data/GNL/log/GNL.log", "r") as fin:
        with open("../runner/GNL_data.json", "w") as fout:
            raw_events = scrape_GNL_events(fin)
            clean_events = {"data": [Event2Dict(e) for e in raw_events]}
            fout.write(json.dumps(clean_events))
     