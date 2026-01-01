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


def main():
    # Metrics across all runs
    agg_delivered_means = []
    agg_unmet_means = []
    agg_fairness_vals = []

    # Data from a representative run (the first one) for plotting
    rep_run_data = None

    print(f"Starting {N_RUNS} independent simulation runs...")

    for run_idx in range(N_RUNS):
        # 1) Init topology from JSON for each run to reset state
        topo, r = init_from_json(TOPOLOGY_FILE)

        # 2) Simulation config
        T = 30  # number of time steps
        times = np.arange(T)

        # Base Demand patterns
        # RX1: slowly increasing demand
        rx1_base = 10 + 2 * times
        # RX2: oscillating around 50
        rx2_base = 50 + 20 * np.sin(times / 3.0)

        # Apply perturbation
        # Noise level: ~10% of demand (std dev)
        # We add Gaussian noise and clamp to >= 0
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

        # Logs for this run
        rx1_received = []
        rx2_received = []
        rx1_demand_log = []
        rx2_demand_log = []
        total_unmet = []
        total_delivered = []

        # Only print detailed logs for the representative run
        is_rep_run = (run_idx == 0)
        if is_rep_run:
            print(f"Run {run_idx+1}/{N_RUNS} (Representative Run) - Init response: {r.json()}")

        for t in range(T):
            d1 = float(rx1_demand[t])
            d2 = float(rx2_demand[t])

            demands = [
                {"rx_id": "RX1", "demand": d1},
                {"rx_id": "RX2", "demand": d2},
            ]

            if is_rep_run:
                print(f"\n=== TIME STEP {t} ===")
                print("Demands:", demands)

            # Choose which policy to test here:
            r_step = requests.post(f"{BASE_URL}/step_fair", json=demands)
            resp = r_step.json()

            if is_rep_run:
                print("Step response (summary):", {
                    "last_step_received": resp.get("last_step_received")
                })

            status = requests.get(f"{BASE_URL}/status").json()
            rec = status["last_step_received"]
            dem = status["last_step_demands"]

            r1_rec = rec.get("RX1", 0.0)
            r2_rec = rec.get("RX2", 0.0)
            r1_dem = dem.get("RX1", 0.0)
            r2_dem = dem.get("RX2", 0.0)

            rx1_received.append(r1_rec)
            rx2_received.append(r2_rec)
            rx1_demand_log.append(r1_dem)
            rx2_demand_log.append(r2_dem)

            delivered = r1_rec + r2_rec
            unmet = max(r1_dem - r1_rec, 0) + max(r2_dem - r2_rec, 0)

            total_delivered.append(delivered)
            total_unmet.append(unmet)

            if is_rep_run:
                print(f"Delivered power: {delivered:.2f}, Unmet demand: {unmet:.2f}")

        # Compute metrics for this run
        run_avg_delivered = float(np.mean(total_delivered))
        run_avg_unmet = float(np.mean(total_unmet))

        # Fairness over total received power in the run
        total_rx1 = sum(rx1_received)
        total_rx2 = sum(rx2_received)
        run_fairness = jains_fairness([total_rx1, total_rx2])

        agg_delivered_means.append(run_avg_delivered)
        agg_unmet_means.append(run_avg_unmet)
        agg_fairness_vals.append(run_fairness)

        if is_rep_run:
            print("\n=== REPRESENTATIVE RUN SUMMARY ===")
            print("Average delivered power:", run_avg_delivered)
            print("Average unmet demand:", run_avg_unmet)
            print("Jain's fairness:", run_fairness)

            rep_run_data = {
                "times": times,
                "rx1_demand_log": rx1_demand_log,
                "rx1_received": rx1_received,
                "rx2_demand_log": rx2_demand_log,
                "rx2_received": rx2_received,
                "total_unmet": total_unmet
            }

    # End of runs
    final_avg_delivered = np.mean(agg_delivered_means)
    final_avg_unmet = np.mean(agg_unmet_means)
    final_avg_fairness = np.mean(agg_fairness_vals)

    print(f"\n=== AGGREGATED SUMMARY (over {N_RUNS} runs) ===")
    print(f"Mean Average Delivered Power: {final_avg_delivered:.2f}")
    print(f"Mean Average Unmet Demand: {final_avg_unmet:.2f}")
    print(f"Mean Fairness: {final_avg_fairness:.4f}")

    # 3) Plotting (using representative run)
    if rep_run_data:
        times = rep_run_data["times"]

        # a) RX1: demand vs received
        plt.figure()
        plt.plot(times, rep_run_data["rx1_demand_log"], label="RX1 demand")
        plt.plot(times, rep_run_data["rx1_received"], label="RX1 received")
        plt.xlabel("Time step")
        plt.ylabel("Power")
        plt.title("RX1: Demand vs Received (Representative Run)")
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(FIGURES_DIR, "rx1_demand_vs_received.png"), dpi=300)
        print("Saved rx1_demand_vs_received.png")

        # b) RX2: demand vs received
        plt.figure()
        plt.plot(times, rep_run_data["rx2_demand_log"], label="RX2 demand")
        plt.plot(times, rep_run_data["rx2_received"], label="RX2 received")
        plt.xlabel("Time step")
        plt.ylabel("Power")
        plt.title("RX2: Demand vs Received (Representative Run)")
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(FIGURES_DIR, "rx2_demand_vs_received.png"), dpi=300)
        print("Saved rx2_demand_vs_received.png")

        # c) Total unmet demand over time
        plt.figure()
        plt.plot(times, rep_run_data["total_unmet"])
        plt.xlabel("Time step")
        plt.ylabel("Unmet demand")
        plt.title("Total Unmet Demand vs Time (Representative Run)")
        plt.grid(True)
        plt.savefig(os.path.join(FIGURES_DIR, "total_unmet_demand_timeseries.png"), dpi=300)
        print("Saved total_unmet_demand_timeseries.png")


if __name__ == "__main__":
    main()
