import requests

BASE_URL = "http://127.0.0.1:8000"


def main():
    # 1. Init basic topology
    r = requests.post(f"{BASE_URL}/init_basic")
    print("Init response:", r.json())

    # 2. Run static allocation
    r = requests.post(f"{BASE_URL}/static_allocate")
    print("Static allocation response:", r.json())

    # 3. Check final status
    r = requests.get(f"{BASE_URL}/status")
    print("Final status:", r.json())


if __name__ == "__main__":
    main()
