from flask import Flask
import os

app = Flask(__name__)

@app.route("/exec_command/<string:command>", methods=["POST"])
def exec_command(command: str):
    os.system("cd .. && " + command)
    return ""

app.run(debug=True, port=3000)