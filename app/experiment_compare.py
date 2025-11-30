import requests
import numpy as np
import matplotlib.pyplot as plt
from .utils_topology import init_from_json

BASE_URL = "http://127.0.0.1:8000"
TOPOLOGY_FILE = "topology_basic.json"


def jains_fairness(values):
    """Compute Jain's fairness index for a list of non-negative values."""
    values = np.array(values, dtype=float)
    if np.all(values == 0):
        return 1.0
    num = (values.sum()) ** 2
    den = len(values) * (values ** 2).sum()
    return float(num / den)


def run_policy(policy_endpoint: str, T: int):
    # Reset topology from JSON for each policy
    init_from_json(TOPOLOGY_FILE)

    times = np.arange(T)
    rx1_demand = 10 + 2 * times
    rx2_demand = 50 + 20 * np.sin(times / 3.0)

    total_unmet = []
    total_delivered = []
    rx1_received_hist = []
    rx2_received_hist = []

    for t in range(T):
        d1 = float(max(rx1_demand[t], 0.0))
        d2 = float(max(rx2_demand[t], 0.0))

        demands = [
            {"rx_id": "RX1", "demand": d1},
            {"rx_id": "RX2", "demand": d2},
        ]

        r = requests.post(f"{BASE_URL}/{policy_endpoint}", json=demands)
        resp = r.json()

        status = requests.get(f"{BASE_URL}/status").json()
        rec = status["last_step_received"]
        dem = status["last_step_demands"]

        r1_rec = rec["RX1"]
        r2_rec = rec["RX2"]
        r1_dem = dem["RX1"]
        r2_dem = dem["RX2"]

        rx1_received_hist.append(r1_rec)
        rx2_received_hist.append(r2_rec)

        delivered = r1_rec + r2_rec
        unmet = max(r1_dem - r1_rec, 0) + max(r2_dem - r2_rec, 0)

        total_delivered.append(delivered)
        total_unmet.append(unmet)

    total_rx1 = sum(rx1_received_hist)
    total_rx2 = sum(rx2_received_hist)
    fairness = jains_fairness([total_rx1, total_rx2])

    return {
        "avg_delivered": float(np.mean(total_delivered)),
        "avg_unmet": float(np.mean(total_unmet)),
        "fairness": fairness,
    }


def main():
    T = 30

    res_dynamic = run_policy("step_dynamic", T)
    res_fair = run_policy("step_fair", T)

    print("Dynamic policy results:", res_dynamic)
    print("Fair policy results:", res_fair)

    policies = ["Dynamic", "Fair"]
    avg_delivered = [res_dynamic["avg_delivered"], res_fair["avg_delivered"]]
    avg_unmet = [res_dynamic["avg_unmet"], res_fair["avg_unmet"]]
    fairness_vals = [res_dynamic["fairness"], res_fair["fairness"]]

    x = np.arange(len(policies))
    width = 0.35

    # 1) Avg delivered
    plt.figure()
    plt.bar(x, avg_delivered, width)
    plt.xticks(x, policies)
    plt.ylabel("Average delivered power")
    plt.title("Average Delivered Power per Policy")
    plt.grid(axis="y")

    # 2) Avg unmet
    plt.figure()
    plt.bar(x, avg_unmet, width)
    plt.xticks(x, policies)
    plt.ylabel("Average unmet demand")
    plt.title("Average Unmet Demand per Policy")
    plt.grid(axis="y")

    # 3) Fairness
    plt.figure()
    plt.bar(x, fairness_vals, width)
    plt.xticks(x, policies)
    plt.ylim(0, 1.1)
    plt.ylabel("Jain's fairness index")
    plt.title("Fairness Comparison per Policy")
    plt.grid(axis="y")

    plt.show()


if __name__ == "__main__":
    main()
