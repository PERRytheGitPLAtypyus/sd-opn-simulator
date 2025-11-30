import requests

BASE_URL = "http://127.0.0.1:8000"


def main():
    # Initialize basic topology
    r = requests.post(f"{BASE_URL}/init_basic")
    print("Init response:", r.json())

    # Define some test demands (time steps)
    # Example: at t0, RX1 wants 20, RX2 wants 80
    #          at t1, RX1 wants 90, RX2 wants 10
    demand_sequences = [
        [
            {"rx_id": "RX1", "demand": 20.0},
            {"rx_id": "RX2", "demand": 80.0},
        ],
        [
            {"rx_id": "RX1", "demand": 90.0},
            {"rx_id": "RX2", "demand": 10.0},
        ],
    ]

    for step_idx, demands in enumerate(demand_sequences):
        print(f"\n=== TIME STEP {step_idx} ===")
        r = requests.post(f"{BASE_URL}/step_dynamic", json=demands)
        print("Dynamic step response:", r.json())

        status = requests.get(f"{BASE_URL}/status").json()
        print("Status last_step_demands:", status["last_step_demands"])
        print("Status last_step_received:", status["last_step_received"])


if __name__ == "__main__":
    main()
