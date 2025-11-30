import json
import requests

BASE_URL = "http://127.0.0.1:8000"


def init_from_json(path: str):
    with open(path, "r") as f:
        topo = json.load(f)
    r = requests.post(f"{BASE_URL}/init_topology", json=topo)
    return topo, r
