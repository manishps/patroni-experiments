import os
from typing import Union

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def kill_process_on_port(port: int, sig: Union[int, None] = None) -> None:
    """
    Kills whatever process is on this port
    BE CAREFUL
    """
    os.system(f"lsof -nti:{port} | xargs kill {sig if sig != None else ''}")

def replace_strs(obj: dict, replacements: list[tuple[str, str]]):
    """
    Helper function to recursively modify strings in a dictionary
    """
    for key in obj:
        val = obj[key]
        if isinstance(val, str):
            for marker, replacement in replacements:
                val = obj[key]
                marker = f"<{marker}>"
                obj[key] = val.replace(marker, replacement)
        if isinstance(val, dict):
            obj[key] = replace_strs(obj[key], replacements)
        if isinstance(val, list):
            new_list = []
            for item in val:
                if not isinstance(item, str):
                    continue
                new_str = item
                for marker, replacement in replacements:
                    marker = f"<{marker}>"
                    new_str = new_str.replace(marker, replacement)
                new_list.append(new_str)
            obj[key] = new_list
    return obj