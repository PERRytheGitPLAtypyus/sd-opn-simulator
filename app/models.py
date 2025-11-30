from pydantic import BaseModel
from typing import Dict, List
from enum import Enum


class Priority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Transmitter(BaseModel):
    id: str
    capacity: float  # max power capacity (arbitrary units)


class Receiver(BaseModel):
    id: str
    priority: Priority
    max_receive: float  # max power it can use at RX side


class Link(BaseModel):
    tx_id: str
    rx_id: str
    efficiency: float  # 0 to 1, path efficiency


class Flow(BaseModel):
    id: str
    tx_id: str
    rx_id: str
    allocated_power: float  # power at transmitter side


class ReceiverDemand(BaseModel):
    rx_id: str
    demand: float  # requested power at receiver side


class NetworkState(BaseModel):
    transmitters: Dict[str, Transmitter]
    receivers: Dict[str, Receiver]
    links: Dict[str, Link]
    flows: Dict[str, Flow]
    last_step_demands: Dict[str, float]
    last_step_received: Dict[str, float]


def link_key(tx_id: str, rx_id: str) -> str:
    return f"{tx_id}->{rx_id}"


class TopologyPayload(BaseModel):
    """
    Used by /init_topology to initialize the network
    from a JSON-defined topology.
    """
    transmitters: List[Transmitter]
    receivers: List[Receiver]
    links: List[Link]
