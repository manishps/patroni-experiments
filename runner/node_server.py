import sys

sys.path.append("..")

import os
from flask import Flask, make_response, jsonify
from log_scraper.log_scraper import scrape_POL_events, scrape_PNL_events
from log_scraper.events import Event2Dict

app = Flask(__name__)


@app.route("/exec_command/<string:command>", methods=["POST"])
def exec_command(command: str):
    os.system("cd .. && " + command)
    return make_response("Executed", 200)

@app.route("/get_logs/<string:type>", methods=["GET"])
def get_logs(type: str):
    raw_events = []
    if type == "POL":
        with open("../patroni/logs/patroni.log", "r") as fin:
            raw_events = scrape_POL_events(fin)
    elif type == "PNL":
        with open("../patroni/logs/patroni.log", "r") as fin:
            raw_events = scrape_PNL_events(fin)
    else:
        return make_response("Invalid log type", 400)
    clean_events = [Event2Dict(e) for e in raw_events]
    return jsonify({"data": clean_events})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3000)