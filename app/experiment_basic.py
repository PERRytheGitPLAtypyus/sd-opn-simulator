import requests
import numpy as np
import matplotlib.pyplot as plt
from .utils_topology import init_from_json

BASE_URL = "http://127.0.0.1:8000"
TOPOLOGY_FILE = "topology_basic.json"


def main():
    # 1) Init topology from JSON
    topo, r = init_from_json(TOPOLOGY_FILE)
    print("Init response:", r.json())

    # 2) Simulation config
    T = 30  # number of time steps
    times = np.arange(T)

    # Demand patterns
    # RX1: slowly increasing demand
    rx1_demand = 10 + 2 * times
    # RX2: oscillating around 50
    rx2_demand = 50 + 20 * np.sin(times / 3.0)

    # Logs
    rx1_received = []
    rx2_received = []
    rx1_demand_log = []
    rx2_demand_log = []
    total_unmet = []
    total_delivered = []

    for t in range(T):
        d1 = float(max(rx1_demand[t], 0.0))
        d2 = float(max(rx2_demand[t], 0.0))

        demands = [
            {"rx_id": "RX1", "demand": d1},
            {"rx_id": "RX2", "demand": d2},
        ]

        print(f"\n=== TIME STEP {t} ===")
        print("Demands:", demands)

        # Choose which policy to test here:
        # r_step = requests.post(f"{BASE_URL}/step_dynamic", json=demands)
        r_step = requests.post(f"{BASE_URL}/step_fair", json=demands)
        resp = r_step.json()
        print("Step response (summary):", {
            "last_step_received": resp["last_step_received"]
        })

        status = requests.get(f"{BASE_URL}/status").json()
        rec = status["last_step_received"]
        dem = status["last_step_demands"]

        r1_rec = rec["RX1"]
        r2_rec = rec["RX2"]
        r1_dem = dem["RX1"]
        r2_dem = dem["RX2"]

        rx1_received.append(r1_rec)
        rx2_received.append(r2_rec)
        rx1_demand_log.append(r1_dem)
        rx2_demand_log.append(r2_dem)

        delivered = r1_rec + r2_rec
        unmet = max(r1_dem - r1_rec, 0) + max(r2_dem - r2_rec, 0)

        total_delivered.append(delivered)
        total_unmet.append(unmet)

        print(f"Delivered power: {delivered:.2f}, Unmet demand: {unmet:.2f}")

    print("\n=== SUMMARY ===")
    print("Average delivered power:", float(np.mean(total_delivered)))
    print("Average unmet demand:", float(np.mean(total_unmet)))

    # 3) Plotting

    # a) RX1: demand vs received
    plt.figure()
    plt.plot(times, rx1_demand_log, label="RX1 demand")
    plt.plot(times, rx1_received, label="RX1 received")
    plt.xlabel("Time step")
    plt.ylabel("Power")
    plt.title("RX1: Demand vs Received")
    plt.legend()
    plt.grid(True)

    # b) RX2: demand vs received
    plt.figure()
    plt.plot(times, rx2_demand_log, label="RX2 demand")
    plt.plot(times, rx2_received, label="RX2 received")
    plt.xlabel("Time step")
    plt.ylabel("Power")
    plt.title("RX2: Demand vs Received")
    plt.legend()
    plt.grid(True)

    # c) Total unmet demand over time
    plt.figure()
    plt.plot(times, total_unmet)
    plt.xlabel("Time step")
    plt.ylabel("Unmet demand")
    plt.title("Total Unmet Demand vs Time")
    plt.grid(True)

    plt.show()


if __name__ == "__main__":
    main()
