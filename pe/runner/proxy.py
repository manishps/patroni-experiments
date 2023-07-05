import os
from pe.utils import ROOT_DIR

def proxy_process(config: str):
    config_file = os.path.join(ROOT_DIR, "runner", "tmp", "proxy" + ".cfg")
    with open(config_file, "w") as fout:
        fout.write(config)
    os.system(f"haproxy -f {config_file} > /dev/null")
    os.system(f"rm {config_file}")