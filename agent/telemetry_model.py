# Create a model here
from dataclasses import dataclass
from .collectors.geolocation import GeoLocation
from typing import List, Optional, Dict

@dataclass
class Telemetry:
    timestamp: float
    target: str
    latency: Optional[float]  # in milliseconds
    packet_loss: Optional[float]  # in percentage
    hop_count: Optional[int]
    hop_list: Optional[List[Dict[str, Any]]]
    geo: Optional[GeoLocation]
    status: str
    error_type: str
    error_detail: str
