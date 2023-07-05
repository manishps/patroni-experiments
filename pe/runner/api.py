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
from pe.runner.proxy import proxy_process
from typing import Union

app = Flask(__name__)

class Api:
    # TODO: Anything cleaner than static?
    etcd_process: Union[multiprocessing.Process, None] = None
    patroni_process: Union[multiprocessing.Process, None] = None
    proxy_process: Union[multiprocessing.Process, None] = None
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
        """
        Helper method to perform a get request to this api
        :param str endpoint: The endpoint to hit (i.e. /endpoint)
        """
        getting = f"http://{self.host}:{self.port}/{endpoint}"
        resp = requests.get(getting)
        if resp.status_code != 200:
            raise ApiError(f"GET {getting} returned {resp.text}")
    
    def post(self, endpoint: str, json={}):
        """
        Helper method to perform a get request to this api
        :param str endpoint: The endpoint to hit (i.e. /endpoint)
        :param dict json: A json body to include in the request
        """ 
        posting = f"http://{self.host}:{self.port}/{endpoint}"
        resp = requests.post(posting, json=json)
        if resp.status_code != 200:
            raise ApiError(f"POST {posting} return {resp.text}")
    
    def serve(self):
        """
        Begin serving the api. Note that this will block, and thus should be
        run in its own process.
        """
        app.run(host="0.0.0.0", port=self.port, debug=False)
    
    """
    Simple ping to make sure the api is up
    """
    @staticmethod
    @app.route("/ping", methods=["GET"])
    def api_ping():
        return make_response("Pong", 200)
    def ping(self):
        self.get("ping")
    
    """
    Wildcard endpoint to execute needed steps
    """
    @staticmethod
    @app.route("/exec_command/<string:command>", methods=["POST"])
    def api_exec_command(command: str):
        os.system(command)
        return make_response("Executed", 200)
    def exec_command(self, command: str):
        self.post(f"exec_command/{command}")
    
    """
    Start etcd locally in a different process
    """
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
        Api.etcd_process = multiprocessing.Process(
            target=etcd_process,
            args=(json["my_name"], topology)
        )
        Api.etcd_process.start()
        return make_response("Etcd started", 200)
    def start_etcd(self, my_name: str, topology: TopologyConfig):
        body = {
            "my_name": my_name,
            "topology": jsonpickle.encode(topology)
        }
        self.post("start_etcd", json=body)
    
    """
    Start patroni locally in a different process
    """
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
        Api.patroni_process = multiprocessing.Process(
            target=patroni_process,
            args=(patroni_dict,)
        )
        Api.patroni_process.start()
        return make_response("Patroni started", 200)
    def start_patroni(self, patroni_dict: dict):
        body = {
            "patroni_dict": jsonpickle.encode(patroni_dict),
        }
        self.post("start_patroni", json=body)
    
    """
    Stop local etcd instances
    """
    @staticmethod
    @app.route("/stop_etcd", methods=["POST"])
    def api_stop_etcd():
        print("here here here")
        if Api.etcd_process:
            Api.etcd_process.terminate()
            Api.etcd_process.join()
            Api.etcd_process = None
            print("killed everything")
        return make_response("Etcd killed", 200)
    def stop_etcd(self):
        self.post("stop_etcd")
    
    """
    Stop local patroni instances
    """
    @staticmethod
    @app.route("/stop_patroni", methods=["POST"])
    def api_stop_patroni():
        if Api.patroni_process:
            Api.patroni_process.terminate()
            Api.patroni_process.join()
            Api.patroni_process = None
        return make_response("Patroni killed", 200)
    def stop_patroni(self):
        self.post("stop_patroni")
    
    """
    Start local proxy instance
    """
    @staticmethod
    @app.route("/start_proxy", methods=["POST"])
    def api_start_proxy():
        json = request.json
        if json == None or json.get("haproxy_conf", None) == None:
            return make_response("Improper json", 503)
        conf = json["haproxy_conf"]

        Api.proxy_process = multiprocessing.Process(
            target=proxy_process,
            args=(conf,)
        )
        Api.proxy_process.start()
        return make_response("Proxy started", 200)
    def start_proxy(self, conf: str):
        body = {
            "haproxy_conf": conf,
        }
        self.post("start_proxy", json=body)
        


if __name__ == "__main__":
    host, port = sys.argv[1:3]
    port = int(port)
    api = Api(host, port)
    api.serve()
