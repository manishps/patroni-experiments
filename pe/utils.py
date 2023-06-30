import os
from typing import Union

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def kill_process_on_port(port: int, sig: Union[int, None] = None) -> None:
    """
    Kills whatever process is on this port
    BE CAREFUL
    """
    os.system(f"lsof -nti:{port} | xargs kill {sig if sig != None else ''}")
