import logging

import jc

from dataclasses import dataclass
from typing import List, Optional, Dict
from .runner import run_command

logger = logging.getLogger("telemetry-agent")


@dataclass
class TracerouteResult:
    hop_count: int
    hop_list: List[Hop]  # List of Hop objects

@dataclass
class Hop:
    hop_number: int
    ip: Optional[str]
    responded: bool
    rtt_avg: Optional[float]  # in milliseconds
    rtt_min: Optional[float]  # in milliseconds
    rtt_max: Optional[float]  # in milliseconds

def convert_traceroute_dict(target: str, traceroute_data: dict) -> TracerouteResult:

    # Check if the traceroute_data dictionary is empty
    if not isinstance(traceroute_data, dict) or not traceroute_data:
        return None

    logger.info(f"{target} -- Converting traceroute data to custom object")

    # Convert the jc output into the custom object and return it
    hop_list = []
    for hop in traceroute_data.get("hops", []):
        hop_number=hop.get("hop")
        rtts = []
        responded_any = False
        ip = None

        for probe in hop.get("probes", []):
            probe_ip = probe.get("ip")
            rtt = probe.get("rtt")
        
            # Track IP if present
            if probe_ip:
                ip = probe_ip

            # Track RTTs
            if rtt is not None:
                rtts.append(rtt)
                responded_any = True

        # Compute summary metrics
        avg_rtt = sum(rtts) / len(rtts) if rtts else None
        min_rtt = min(rtts) if rtts else None
        max_rtt = max(rtts) if rtts else None

        hop_obj = Hop(
            hop_number=hop_number,
            ip=ip,
            responded=responded_any,
            rtt_avg=avg_rtt,
            rtt_min=min_rtt,
            rtt_max=max_rtt
        )
        hop_list.append(hop_obj)

    return TracerouteResult(
        hop_count=len(hop_list),
        hop_list=hop_list
    )

def collect_traceroute_data(target: str) -> TracerouteResult:
    """Run traceroute command and return hop data using jc parser."""
    logger.info(f"{target} -- Running traceroute command")

    try:
        output = run_command(target, "traceroute", f"{target} 2>&1")
        if output is None:
            return None

        logger.info(f"{target} -- Parsing traceroute data using JSON Convert (jc)")

        traceroute_data = jc.parse('traceroute', output)

        # Use for debugging purposes
        # logger.info(f"Traceroute Result:")
        # logger.info("--------------------------")
        # logger.info(traceroute_data)

    except Exception as e:
        logger.error(f"{target} -- Error running traceroute: {e}")
        return None

    return convert_traceroute_dict(target, traceroute_data)
