import requests
import numpy as np
import matplotlib.pyplot as plt
import os
from .utils_topology import init_from_json

BASE_URL = "http://127.0.0.1:8000"
TOPOLOGY_FILE = "topology_basic.json"
N_RUNS = 20
FIGURES_DIR = "results/figures"

# Ensure figures directory exists
os.makedirs(FIGURES_DIR, exist_ok=True)


def jains_fairness(values):
    """Compute Jain's fairness index for a list of non-negative values."""
    values = np.array(values, dtype=float)
    if np.all(values == 0):
        return 1.0
    num = (values.sum()) ** 2
    den = len(values) * (values ** 2).sum()
    return float(num / den)


def run_policy(policy_endpoint: str, T: int):
    # Store metrics for each run
    run_avg_delivered = []
    run_avg_unmet = []
    run_fairness = []

    print(f"Running policy '{policy_endpoint}' over {N_RUNS} runs...")

    for run_idx in range(N_RUNS):
        # Reset topology from JSON for each run
        init_from_json(TOPOLOGY_FILE)

        times = np.arange(T)
        rx1_base = 10 + 2 * times
        rx2_base = 50 + 20 * np.sin(times / 3.0)

        # Apply perturbation
        rx1_demand = []
        rx2_demand = []
        for val in rx1_base:
            noise = np.random.normal(0, 0.1 * abs(val))
            rx1_demand.append(max(val + noise, 0.0))
        for val in rx2_base:
            noise = np.random.normal(0, 0.1 * abs(val))
            rx2_demand.append(max(val + noise, 0.0))

        rx1_demand = np.array(rx1_demand)
        rx2_demand = np.array(rx2_demand)

        total_unmet = []
        total_delivered = []
        rx1_received_hist = []
        rx2_received_hist = []

        for t in range(T):
            d1 = float(rx1_demand[t])
            d2 = float(rx2_demand[t])

            demands = [
                {"rx_id": "RX1", "demand": d1},
                {"rx_id": "RX2", "demand": d2},
            ]

            r = requests.post(f"{BASE_URL}/{policy_endpoint}", json=demands)
            resp = r.json()

            status = requests.get(f"{BASE_URL}/status").json()
            rec = status["last_step_received"]
            dem = status["last_step_demands"]

            r1_rec = rec.get("RX1", 0.0)
            r2_rec = rec.get("RX2", 0.0)
            r1_dem = dem.get("RX1", 0.0)
            r2_dem = dem.get("RX2", 0.0)

            rx1_received_hist.append(r1_rec)
            rx2_received_hist.append(r2_rec)

            delivered = r1_rec + r2_rec
            unmet = max(r1_dem - r1_rec, 0) + max(r2_dem - r2_rec, 0)

            total_delivered.append(delivered)
            total_unmet.append(unmet)

        # Metrics for this run
        run_avg_delivered.append(float(np.mean(total_delivered)))
        run_avg_unmet.append(float(np.mean(total_unmet)))

        total_rx1 = sum(rx1_received_hist)
        total_rx2 = sum(rx2_received_hist)
        run_fairness.append(jains_fairness([total_rx1, total_rx2]))

    # Aggregate
    return {
        "avg_delivered": float(np.mean(run_avg_delivered)),
        "avg_unmet": float(np.mean(run_avg_unmet)),
        "fairness": float(np.mean(run_fairness)),
    }


def main():
    T = 30

    res_dynamic = run_policy("step_dynamic", T)
    res_fair = run_policy("step_fair", T)

    print(f"Dynamic policy results (avg over {N_RUNS} runs):", res_dynamic)
    print(f"Fair policy results (avg over {N_RUNS} runs):", res_fair)

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
    plt.title(f"Average Delivered Power per Policy\n(Mean of {N_RUNS} Runs)")
    plt.grid(axis="y")
    plt.savefig(os.path.join(FIGURES_DIR, "avg_delivered_power_per_policy.png"), dpi=300)
    print("Saved avg_delivered_power_per_policy.png")

    # 2) Avg unmet
    plt.figure()
    plt.bar(x, avg_unmet, width)
    plt.xticks(x, policies)
    plt.ylabel("Average unmet demand")
    plt.title(f"Average Unmet Demand per Policy\n(Mean of {N_RUNS} Runs)")
    plt.grid(axis="y")
    plt.savefig(os.path.join(FIGURES_DIR, "avg_unmet_demand_per_policy.png"), dpi=300)
    print("Saved avg_unmet_demand_per_policy.png")

    # 3) Fairness
    plt.figure()
    plt.bar(x, fairness_vals, width)
    plt.xticks(x, policies)
    plt.ylim(0, 1.1)
    plt.ylabel("Jain's fairness index")
    plt.title(f"Fairness Comparison per Policy\n(Mean of {N_RUNS} Runs)")
    plt.grid(axis="y")
    plt.savefig(os.path.join(FIGURES_DIR, "fairness_per_policy.png"), dpi=300)
    print("Saved fairness_per_policy.png")


if __name__ == "__main__":
    main()
