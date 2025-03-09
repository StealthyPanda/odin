
from dataclasses import dataclass



@dataclass
class DeviceData:
    memory : int
    name : str
    int_name : str


@dataclass
class NodeData:
    machine : str
    host : str
    devices : list[DeviceData]

