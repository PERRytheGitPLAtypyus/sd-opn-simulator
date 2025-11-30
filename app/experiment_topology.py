import requests
import json
import numpy as np

BASE_URL = "http://127.0.0.1:8000"
TOPOLOGY_FILE = "topology_basic.json"


def main():
    # Load topology from JSON file
    with open(TOPOLOGY_FILE, "r") as f:
        topo = json.load(f)

    # Initialize controller with this topology
    r = requests.post(f"{BASE_URL}/init_topology", json=topo)
    print("Init_topology response:", r.status_code, r.text)

    if r.status_code != 200:
        print("Error during init_topology, aborting.")
        return

    # Simple test run using dynamic policy
    T = 10
    times = np.arange(T)
    rx_ids = [rx["id"] for rx in topo["receivers"]]

    # For simplicity, assume exactly 2 receivers: RX1, RX2
    rx1_id, rx2_id = rx_ids[0], rx_ids[1]

    rx1_demand = 10 + 2 * times
    rx2_demand = 50 + 20 * np.sin(times / 3.0)

    for t in range(T):
        d1 = float(max(rx1_demand[t], 0.0))
        d2 = float(max(rx2_demand[t], 0.0))

        demands = [
            {"rx_id": rx1_id, "demand": d1},
            {"rx_id": rx2_id, "demand": d2},
        ]

        print(f"\n=== TIME STEP {t} ===")
        print("Demands:", demands)

        r = requests.post(f"{BASE_URL}/step_dynamic", json=demands)

        print("HTTP status from /step_dynamic:", r.status_code)
        print("Raw response text:", r.text)

        # Safely handle JSON / non-JSON
        if r.headers.get("content-type", "").startswith("application/json"):
            try:
                resp = r.json()
            except Exception as e:
                print("Failed to parse JSON:", e)
                break
            print("Parsed JSON:", resp)
            if "last_step_received" in resp:
                print("Step received:", resp["last_step_received"])
        else:
            print("Non-JSON response from server, stopping.")
            break

    print("\nDone topology-based test.")


if __name__ == "__main__":
    main()
