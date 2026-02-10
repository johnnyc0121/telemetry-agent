import jc
import logging

from dataclasses import dataclass
from .runner import run_command

logger = logging.getLogger("telemetry-agent")


@dataclass
class PingResult:
    latency: float  # in milliseconds
    packet_loss: float  # in percentage

def convert_ping_dict(target: str, ping_data: dict) -> PingResult:
    if not isinstance(ping_data, dict) or not ping_data:
        return None

    logger.info(f"{target} -- Converting ping data to custom object")

    latency = ping_data.get("round_trip_ms_avg")
    packet_loss = ping_data.get("packet_loss_percent")

    return PingResult(
        latency=latency,
        packet_loss=packet_loss
    )

def collect_ping_data(target: str) -> PingResult:
    """Run ping command return detailed statistics using jc parser."""
    logger.info(f"{target} -- Running ping command")

    try:
        output = run_command(target, "ping", f"-c 4 {target}")
        if output is None:
            return None

        logger.info(f"{target} -- Parsing ping data using JSON Convert (jc)")

        ping_data = jc.parse('ping', output)

        # Use for debugging purposes
        # logger.info(f"Ping Result:")
        # logger.info("--------------------------")
        # logger.info(ping_data)

    except Exception as e:
        logger.error(f"{target} -- Error running ping: {e}")
        return None

    return convert_ping_dict(target, ping_data)