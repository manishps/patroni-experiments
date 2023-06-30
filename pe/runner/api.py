import os
import sys
import requests
import jsonpickle
import multiprocessing
from datetime import datetime
from flask import Flask, make_response, jsonify, request
from pe.config.parse import TopologyConfig
from pe.exceptions import ApiError
from pe.log_scraper.log_scraper import scrape_POL_events, scrape_PNL_events, scrape_GOL_events, scrape_GNL_events
from pe.log_scraper.events import Event2Dict
from pe.runner.etcd import etcd_process
from pe.runner.patroni import patroni_process

app = Flask(__name__)

class Api:
    """
    A class to manage the controller api on each agent. This class has
    BOTH the code to actually run the flask app AND interact with it
    from the orchestrator.
    :param str host: ip of this api
    :param int port: port of this api
    """
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
    
    def get(self, endpoint: str):
        getting = f"http://{self.host}:{self.port}/{endpoint}"
        resp = requests.get(getting)
        if resp.status_code != 200:
            raise ApiError(f"GET {getting} returned {resp.text}")
    
    def post(self, endpoint: str, json={}):
        posting = f"http://{self.host}:{self.port}/{endpoint}"
        resp = requests.post(posting, json=json)
        if resp.status_code != 200:
            raise ApiError(f"POST {posting} return {resp.text}")
    
    def serve(self):
        app.run(host="0.0.0.0", port=self.port, debug=False)
    
    @staticmethod
    @app.route("/ping", methods=["GET"])
    def api_ping():
        return make_response("Pong", 200)
    def ping(self):
        self.get("ping")
    
    @staticmethod
    @app.route("/exec_command/<string:command>", methods=["POST"])
    def api_exec_command(command: str):
        os.system(command)
        return make_response("Executed", 200)
    def exec_command(self, command: str):
        self.post(f"exec_command/{command}")
    
    @staticmethod
    @app.route("/start_etcd", methods=["POST"])
    def api_start_etcd():
        json = request.json
        if json == None or json.get("topology", None) == None or json.get("my_name", None) == None:
            return make_response("Improper json", 503)
        raw_topology = json["topology"]
        topology = jsonpickle.decode(raw_topology)
        if not isinstance(topology, TopologyConfig):
            return make_response("Improper json", 503)
        multiprocessing.Process(
            target=etcd_process,
            args=(json["my_name"], topology)
        ).start()
        return make_response("Etcd started", 200)
    def start_etcd(self, my_name: str, topology: TopologyConfig):
        body = {
            "my_name": my_name,
            "topology": jsonpickle.encode(topology)
        }
        self.post("start_etcd", json=body)
    
    @staticmethod
    @app.route("/start_patroni", methods=["POST"])
    def api_start_patroni():
        json = request.json
        if json == None or json.get("patroni_dict", None) == None:
            return make_response("Improper json", 503)
        raw_patroni_dict = json["patroni_dict"]
        patroni_dict = jsonpickle.decode(raw_patroni_dict)
        if not isinstance(patroni_dict, dict):
            return make_response("Improper json", 503)
        multiprocessing.Process(
            target=patroni_process,
            args=(patroni_dict,)
        ).start()
        return make_response("Patroni started", 200)
    def start_patroni(self, patroni_dict: dict):
        body = {
            "patroni_dict": jsonpickle.encode(patroni_dict),
        }
        self.post("start_patroni", json=body)

if __name__ == "__main__":
    host, port = sys.argv[1:3]
    port = int(port)
    api = Api(host, port)
    api.serve()
