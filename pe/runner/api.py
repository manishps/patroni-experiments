import os
import sys
import requests
import jsonpickle
from flask import Flask, make_response, jsonify, request
from pe.config.parse import TopologyConfig
from pe.exceptions import ApiError
from pe.runner.controllers import EtcdController, PatroniController, ProxyController
from pe.utils import ROOT_DIR
from typing import Union

app = Flask(__name__)

class Api:
    # TODO: Anything cleaner than static?
    etcd_controller: EtcdController = EtcdController()
    patroni_controller: PatroniController = PatroniController()
    proxy_controller: ProxyController = ProxyController()
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
        return resp.text
    
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
        Api.etcd_controller.start({
            "my_name": json["my_name"],
            "topology": topology,
        })
        return make_response("Etcd started", 200)
    def start_etcd(self, my_name: str, topology: TopologyConfig):
        body = {
            "my_name": my_name,
            "topology": jsonpickle.encode(topology)
        }
        self.post("start_etcd", json=body)
    
    """
    Stop local etcd instances
    """
    @staticmethod
    @app.route("/stop_etcd", methods=["POST"])
    def api_stop_etcd():
        Api.etcd_controller.stop()
        return make_response("Etcd killed", 200)
    def stop_etcd(self):
        self.post("stop_etcd")
    
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
        Api.patroni_controller.start(patroni_dict)
        return make_response("Patroni started", 200)
    def start_patroni(self, patroni_dict: dict):
        body = {
            "patroni_dict": jsonpickle.encode(patroni_dict),
        }
        self.post("start_patroni", json=body)
    
    """
    Stop local patroni instances
    """
    @staticmethod
    @app.route("/stop_patroni", methods=["POST"])
    def api_stop_patroni():
        Api.patroni_controller.stop()    
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
        Api.proxy_controller.start(conf)
        return make_response("Proxy started", 200)
    def start_proxy(self, conf: str):
        body = {
            "haproxy_conf": conf,
        }
        self.post("start_proxy", json=body)
    
    """
    Stop a local proxy instance
    """
    @staticmethod
    @app.route("/stop_proxy", methods=["POST"])
    def api_stop_proxy():
        Api.proxy_controller.stop()
        return make_response("Proxy killed", 200)
    def stop_proxy(self):
        self.post("stop_proxy")

    """
    Fetch the contents of a file
    """
    @staticmethod
    @app.route("/fetch_file", methods=["POST"])
    def api_fetch_file():
        json = request.json
        path = json.get("path") if json else None
        if path == None:
            return make_response("Improper json", 503)
        with open(os.path.join(ROOT_DIR, path)) as fin:
            return make_response(fin.read(), 200)
    def fetch_file(self, path: str):
        return self.post("fetch_file", json={"path": path})
    
    """
    Fetch all logs in a folder (appending them together)
    """
    @staticmethod
    @app.route("/fetch_folder", methods=["POST"])
    def api_fetch_folder():
        json = request.json
        path = json.get("path") if json else None
        if path == None:
            return make_response("Path does not exist")
        files = sorted(os.listdir(path))
        result = ""
        for file in files:
            with open(os.path.join(path, file)) as fin:
                result += fin.read()
        return result
    def fetch_folder(self, folder: str):
        return self.post("fetch_folder", json={"path": folder})


if __name__ == "__main__":
    host, port = sys.argv[1:3]
    port = int(port)
    api = Api(host, port)
    api.serve()
