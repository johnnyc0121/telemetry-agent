import argparse
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone

import toml

from .collectors.ping import collect_ping_data
from .collectors.traceroute import collect_traceroute_data
from .collectors.geolocation import collect_geolocation_data
from .telemetry_model import Telemetry
from .influx import InfluxDataWriter
from .utils.config_loader import load_config
from .utils.logger import setup_logging

logger = setup_logging()

def collect_for_target(target, data_writer):
    logger.info(f"{target} -- Collecting telemetry data for target")

    # Create initial snapshot object
    snapshot = Telemetry(
        timestamp=datetime.now(timezone.utc),
        target=target,
        latency=-1.0,
        packet_loss=100.0,
        hop_count=-1,
        hop_list=[],
        geo={},
        status="",
        error_type="",
        error_detail=""
    )

    # Get geolocation result
    geolocation_result = collect_geolocation_data(target)
    if geolocation_result:
        snapshot.geo = asdict(geolocation_result)
    else:
        logger.error(f"{target} -- Failed to get geolocation data for target")
        snapshot.error_type = "geolocation_failed"
        snapshot.error_detail = "Geolocation data could not be obtained"

    # Get ping result
    ping_result = collect_ping_data(target)
    if ping_result:
        snapshot.latency = ping_result.latency
        snapshot.packet_loss = ping_result.packet_loss
    else:
        logger.error(f"{target} -- Failed to get ping result for target")
        snapshot.status = "unreachable"
        snapshot.error_type = "ping_failed"
        snapshot.error_detail = "No response"
        if data_writer is not None:
            data_writer.write_to_influxdb(snapshot)
        return

    # Get traceroute result
    traceroute_result = collect_traceroute_data(target)
    if traceroute_result:
        snapshot.hop_count = traceroute_result.hop_count
        snapshot.hop_list = [asdict(hop) for hop in traceroute_result.hop_list]
    else:
        logger.error(f"{target} -- Failed to get traceroute result for target")
        snapshot.status = "degraded"
        snapshot.error_type = "traceroute_failed"
        snapshot.error_detail = "Traceroute failed to execute"

    # Update status prior to writing the snapshot data to the InfluxDB
    snapshot.status = "ok"

    # Use for debugging purposes
    # logger.info(f"Telemetry data:")
    # logger.info("--------------------------")
    # logger.info(snapshot)

    # Write to the InfluxDB if database option has not been disabled via argument
    if data_writer is not None:
        data_writer.write_to_influxdb(snapshot)

    return snapshot

def main():
    # Main function, set up variables
    collection_interval = int(os.getenv("COLLECTION_INTERVAL", "60"))
    data_writer = None

    # Set up logging
    logger = setup_logging()

    # Get arguments from the command line, if used
    parser = argparse.ArgumentParser(description="Telemetry Agent")
    parser.add_argument(
        "--targets",
        help="Hostnames or IP addresses to run telemetry against"
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Disable writing telemetry to the database"
    )

    args = parser.parse_args()

    # For targets value, CLI takes precedence over the environment variable
    targets_arg = args.targets or os.getenv("TARGETS")

    if not targets_arg:
        logger.error("No targets specified.  Provide --target or set TARGETS environment variable.")
        raise SystemExit(1)

    # Create object to store targets
    targets = targets_arg.split(",")

    config = load_config(os.path.join(os.path.dirname(__file__), 'settings.yaml'))

    # Get database variable
    disable_db = args.no_db

    # Set up database variables if not disabled
    if not disable_db:

        # Obtain token from the InfluxDB configuration file
        with open('/etc/influxdb2/influx-configs', 'r') as file:
            token_config = toml.load(file)

        token = token_config.get('default', {}).get('token', '')

        if token:
            logger.info(f"Using token from InfluxDB config file.")
        else:
            logger.error("Token not found in environment variable or config file.")
            raise SystemExit(1)

        # Create data writer instance
        data_writer = InfluxDataWriter(
            url=os.getenv("INFLUXDB_URL"),
            org=os.getenv("INFLUXDB_ORG"),
            token=token,
            bucket=os.getenv("INFLUXDB_BUCKET")
        )

    logger.info(f"DB writes disabled: {disable_db}")

    # Start the telemetry collection loop
    try:
        while True:
            with ThreadPoolExecutor(max_workers=len(targets)) as executor:
                futures = {
                    executor.submit(collect_for_target, target, data_writer): target
                    for target in targets
                }

                for future in as_completed(futures):
                    target = futures[future]
                    try:
                        result = future.result()
                        if result is None:
                            logger.error(f"{target} -- Telemetry collection failed")
                    except Exception as e:
                        logger.error(f"{target} -- Error during telemetry collection: {e}")

            logger.info(f"Sleeping for {collection_interval} seconds before next collection.")
            time.sleep(collection_interval)

    except KeyboardInterrupt:
        logger.info("Telemetry agent interrupted by user. Exiting...")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        if data_writer is not None:
            try:
                data_writer.close()
            except Exception as e:
                logger.warning(f"Error closing the data writer: {e}")
        logger.info("Telemetry agent has shut down.")

if __name__ == "__main__":
    main()
