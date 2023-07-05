import os
import yaml
from pe.config.parse import NodeConfig, TopologyConfig
from pe.exceptions import BootError
from pe.utils import kill_process_on_port, ROOT_DIR
from typing import Union

def patroni_process(config: dict):
    # Kill any programs on needed ports
    for conn_str in [config["postgresql"]["connect_address"], config["restapi"]["connect_address"]]:
        port = int(conn_str.split(":")[1])
        kill_process_on_port(port)

    config_file = os.path.join(ROOT_DIR, "runner", "tmp", "patroni_" + config["name"] + ".yml")
    with open(config_file, "w") as fout:
        fout.write(yaml.safe_dump(config))
    os.system(f"patroni {config_file} > /dev/null")
    os.system(f"rm {config_file}")
