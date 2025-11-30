from fastapi import FastAPI
from typing import Dict, List
from .models import (
    Transmitter,
    Receiver,
    Link,
    Flow,
    NetworkState,
    ReceiverDemand,
    link_key,
    Priority,
    TopologyPayload,
)
import uuid

app = FastAPI(title="SD-OPN Controller")

# Global in-memory state
state: NetworkState = NetworkState(
    transmitters={},
    receivers={},
    links={},
    flows={},
    last_step_demands={},
    last_step_received={},
)


def _apply_flows_and_update_received() -> None:
    """
    Internal helper:
    - Given current flows, compute received power at each Rx.
    """
    rx_received: Dict[str, float] = {rx_id: 0.0 for rx_id in state.receivers.keys()}

    for flow in state.flows.values():
        lk = link_key(flow.tx_id, flow.rx_id)
        link = state.links.get(lk)
        if not link:
            continue
        p_rx = flow.allocated_power * link.efficiency
        rx_received[flow.rx_id] += p_rx

    state.last_step_received = rx_received


@app.get("/")
def root():
    return {"message": "SD-OPN Controller running"}


@app.post("/init_basic")
def init_basic_topology():
    """
    Initialize ONE Tx and TWO Rx with fixed example values.
    This is your minimal 1 Tx / 2 Rx testbed.
    """
    global state

    tx = Transmitter(id="TX1", capacity=100.0)

    rx1 = Receiver(id="RX1", priority=Priority.HIGH, max_receive=80.0)
    rx2 = Receiver(id="RX2", priority=Priority.MEDIUM, max_receive=50.0)

    link1 = Link(tx_id="TX1", rx_id="RX1", efficiency=0.8)
    link2 = Link(tx_id="TX1", rx_id="RX2", efficiency=0.6)

    state.transmitters = {tx.id: tx}
    state.receivers = {rx1.id: rx1, rx2.id: rx2}
    state.links = {
        link_key(link1.tx_id, link1.rx_id): link1,
        link_key(link2.tx_id, link2.rx_id): link2,
    }
    state.flows = {}
    state.last_step_demands = {}
    state.last_step_received = {rx_id: 0.0 for rx_id in state.receivers.keys()}

    return {
        "status": "initialized",
        "tx": state.transmitters,
        "rx": state.receivers,
    }


@app.post("/init_topology")
def init_topology(payload: TopologyPayload):
    """
    Initialize network from a JSON topology payload.

    Example payload shape:
    {
      "transmitters": [ { "id": "TX1", "capacity": 100.0 } ],
      "receivers": [
        { "id": "RX1", "priority": "HIGH", "max_receive": 80.0 },
        { "id": "RX2", "priority": "MEDIUM", "max_receive": 50.0 }
      ],
      "links": [
        { "tx_id": "TX1", "rx_id": "RX1", "efficiency": 0.8 },
        { "tx_id": "TX1", "rx_id": "RX2", "efficiency": 0.6 }
      ]
    }
    """
    global state

    tx_map = {tx.id: tx for tx in payload.transmitters}
    rx_map = {rx.id: rx for rx in payload.receivers}
    link_map = {link_key(l.tx_id, l.rx_id): l for l in payload.links}

    state.transmitters = tx_map
    state.receivers = rx_map
    state.links = link_map
    state.flows = {}
    state.last_step_demands = {}
    state.last_step_received = {rx_id: 0.0 for rx_id in state.receivers.keys()}

    return {
        "status": "initialized_from_topology",
        "transmitters": state.transmitters,
        "receivers": state.receivers,
        "links": state.links,
    }


@app.get("/status")
def get_status():
    """
    Return current state snapshot.
    """
    return {
        "transmitters": state.transmitters,
        "receivers": state.receivers,
        "links": state.links,
        "flows": state.flows,
        "last_step_demands": state.last_step_demands,
        "last_step_received": state.last_step_received,
    }


@app.post("/static_allocate")
def static_allocate():
    """
    Static policy:
    - Split TX1 capacity between RX1 and RX2 in a fixed ratio (60:40).
    - No consideration of demand.
    """
    global state

    if "TX1" not in state.transmitters:
        return {"error": "Call /init_basic or /init_topology with TX1 first"}

    tx = state.transmitters["TX1"]
    total_power = tx.capacity

    alloc_rx1 = 0.6 * total_power
    alloc_rx2 = 0.4 * total_power

    state.flows = {}

    flow1 = Flow(
        id=str(uuid.uuid4()),
        tx_id="TX1",
        rx_id="RX1",
        allocated_power=alloc_rx1,
    )
    flow2 = Flow(
        id=str(uuid.uuid4()),
        tx_id="TX1",
        rx_id="RX2",
        allocated_power=alloc_rx2,
    )

    state.flows[flow1.id] = flow1
    state.flows[flow2.id] = flow2

    _apply_flows_and_update_received()

    return {
        "status": "static_allocation_done",
        "flows": state.flows,
        "last_step_received": state.last_step_received,
    }


@app.post("/step_dynamic")
def step_dynamic(demands: List[ReceiverDemand]):
    """
    Greedy dynamic policy:
    - Sort receivers by demand (highest first).
    - Allocate TX1 capacity greedily.
    """
    global state

    if "TX1" not in state.transmitters:
        return {"error": "Call an init endpoint first"}

    tx = state.transmitters["TX1"]
    remaining_tx_power = tx.capacity

    state.last_step_demands = {d.rx_id: d.demand for d in demands}

    sorted_demands = sorted(demands, key=lambda d: d.demand, reverse=True)

    state.flows = {}

    for d in sorted_demands:
        if remaining_tx_power <= 0:
            break

        if d.rx_id not in state.receivers:
            continue

        rx = state.receivers[d.rx_id]
        link = state.links.get(link_key(tx.id, rx.id))
        if not link:
            continue

        required_tx_power = d.demand / link.efficiency
        allocated = min(
            remaining_tx_power,
            required_tx_power,
            rx.max_receive / link.efficiency,
        )

        if allocated <= 0:
            continue

        flow = Flow(
            id=str(uuid.uuid4()),
            tx_id=tx.id,
            rx_id=rx.id,
            allocated_power=allocated,
        )
        state.flows[flow.id] = flow
        remaining_tx_power -= allocated

    _apply_flows_and_update_received()

    return {
        "status": "dynamic_step_done",
        "flows": state.flows,
        "last_step_demands": state.last_step_demands,
        "last_step_received": state.last_step_received,
    }


@app.post("/step_fair")
def step_fair(demands: List[ReceiverDemand]):
    """
    Proportional fairness policy:
    - Allocate power proportional to demand,
      capped by max_receive and TX capacity.
    """
    global state

    if "TX1" not in state.transmitters:
        return {"error": "Call an init endpoint first"}

    tx = state.transmitters["TX1"]
    total_tx_capacity = tx.capacity

    state.last_step_demands = {d.rx_id: d.demand for d in demands}

    valid = []
    for d in demands:
        if d.rx_id not in state.receivers:
            continue
        rx = state.receivers[d.rx_id]
        link = state.links.get(link_key(tx.id, rx.id))
        if not link:
            continue
        valid.append((d, rx, link))

    if not valid:
        state.flows = {}
        state.last_step_received = {rx_id: 0.0 for rx_id in state.receivers.keys()}
        return {
            "status": "fair_step_done",
            "flows": state.flows,
            "last_step_demands": state.last_step_demands,
            "last_step_received": state.last_step_received,
        }

    total_demand = sum(d.demand for (d, _, _) in valid)
    if total_demand <= 0:
        state.flows = {}
        state.last_step_received = {rx_id: 0.0 for rx_id in state.receivers.keys()}
        return {
            "status": "fair_step_done",
            "flows": state.flows,
            "last_step_demands": state.last_step_demands,
            "last_step_received": state.last_step_received,
        }

    state.flows = {}
    remaining_tx_power = total_tx_capacity

    provisional_allocs = []
    for (d, rx, link) in valid:
        share_rx = (d.demand / total_demand) * total_tx_capacity * link.efficiency
        share_rx = min(share_rx, d.demand, rx.max_receive)
        share_tx = share_rx / link.efficiency if link.efficiency > 0 else 0.0
        provisional_allocs.append((d.rx_id, share_tx, rx, link))

    total_provisional_tx = sum(a[1] for a in provisional_allocs)
    scale = 1.0
    if total_provisional_tx > total_tx_capacity and total_provisional_tx > 0:
        scale = total_tx_capacity / total_provisional_tx

    rx_received = {rx_id: 0.0 for rx_id in state.receivers.keys()}

    for rx_id, share_tx, rx, link in provisional_allocs:
        alloc_tx = min(share_tx * scale, remaining_tx_power)
        if alloc_tx <= 0:
            continue

        flow = Flow(
            id=str(uuid.uuid4()),
            tx_id=tx.id,
            rx_id=rx_id,
            allocated_power=alloc_tx,
        )
        state.flows[flow.id] = flow
        remaining_tx_power -= alloc_tx

        p_rx = alloc_tx * link.efficiency
        rx_received[rx_id] += p_rx

    state.last_step_received = rx_received

    return {
        "status": "fair_step_done",
        "flows": state.flows,
        "last_step_demands": state.last_step_demands,
        "last_step_received": state.last_step_received,
    }
