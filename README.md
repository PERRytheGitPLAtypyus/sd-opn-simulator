# Software-Defined Optical Power Network (SD-OPN)

A simulation framework that applies Software-Defined Networking (SDN) concepts to optical power distribution.  
The system cleanly separates decision-making (control plane) from energy transfer behavior (data plane), enabling flexible policies, configurable topologies, and reproducible experiments.

---

## Features

### 1. Decoupled Architecture
- **Control Plane**: FastAPI controller responsible for flow allocation decisions.
- **Data Plane**: Simulated transmitters, receivers, and optical links.
- **Topology**: Loaded dynamically from JSON files.

### 2. JSON-Configurable Network Maps
Define the full network structure (Tx, Rx, efficiencies) using files such as:
topology_basic.json

markdown
Copy code

### 3. Power Allocation Policies
Two built-in allocation policies:
- **Dynamic (Greedy)**: Tries to satisfy high-priority or high-demand receivers first.
- **Fair (Proportional)**: Distributes power proportionally to demand.

### 4. Simulation Tools
Scripts included:
- `experiment_basic.py`  
  Runs a 30-step simulation with demand curves and produces plots.
- `experiment_compare.py`  
  Runs both policies, computes metrics:
  - Average delivered power
  - Average unmet demand
  - Jain’s fairness index

### 5. Metrics & Visualization
Produces graphs of:
- Demand vs Received (per receiver)
- Unmet demand over time
- Performance comparison between policies

---

## Installation

1. Clone the repository:
git clone <your-repo-url>

markdown
Copy code

2. Install dependencies:
pip install -r requirements.txt

markdown
Copy code

3. Start the controller:
uvicorn app.controller:app --reload

yaml
Copy code

---

## Running Simulations

### Basic experiment:
python -m app.experiment_basic

shell
Copy code

### Policy comparison:
python -m app.experiment_compare

shell
Copy code

### JSON-topology-based simulation:
python -m app.experiment_topology

yaml
Copy code

---

## Project Structure

app/
controller.py # Control-plane logic (FastAPI)
models.py # Pydantic network models
utils_topology.py # JSON topology loader
experiment_basic.py
experiment_compare.py
experiment_topology.py
topology_basic.json
requirements.txt
README.md

yaml
Copy code

---

## Outputs

- Average delivered power
- Average unmet demand
- Jain’s fairness index
- PNG visualizations of demand curves, allocations, and policy comparisons

---

## Status

Core system complete:
- JSON topology parsing  
- Controller + policies  
- 3 experiment pipelines  
- Plotting + metrics  

Optional future extensions:
- N-receiver generalization  
- Priority-weighted fairness models  

---

## License

Open-source, for academic and research use.