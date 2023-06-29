import os
import sys
from flask import Flask, make_response, jsonify
from pe.log_scraper.log_scraper import scrape_POL_events, scrape_PNL_events, scrape_GOL_events, scrape_GNL_events
from pe.log_scraper.events import Event2Dict
from datetime import datetime
import requests

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
    
    def serve(self):
        app.run(host="0.0.0.0", port=self.port, debug=False)
    
    @staticmethod
    @app.route("/exec_command/<string:command>", methods=["POST"])
    def api_exec_command(command: str):
        os.system(command)
        return make_response("Executed", 200)
    def exec_command(self, command: str):
        requests.post(f"http://{self.host}:{self.port}/exec_command/{command}")
    

if __name__ == "__main__":
    host, port = sys.argv[1:3]
    port = int(port)
    api = Api(host, port)
    api.serve()
