import json
import logging

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

logger = logging.getLogger("telemetry-agent")

class InfluxDataWriter:
    def __init__(self, url, org, token, bucket):
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.org = org
        self.bucket = bucket
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def write_to_influxdb(self, snapshot):
        point = (
            Point("telemetry")
                .tag("target", snapshot.target)
                .field("latency", snapshot.latency)
                .field("packet_loss", snapshot.packet_loss)
                .field("hop_count", snapshot.hop_count)
                .field("hop_list", json.dumps(snapshot.hop_list))
                .field("geo", str(snapshot.geo))
                .field("status", str(snapshot.status))
                .field("error_type", str(snapshot.error_type))
                .field("error_detail", str(snapshot.error_detail))
                .time(snapshot.timestamp, WritePrecision.NS)
        )

        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            logger.info(f"{snapshot.target} -- Wrote telemetry data to InfluxDB.")
        except Exception as e:
            logger.error(f"{snapshot.target} -- Failed to write telemetry data to InfluxDB: {e}")

    def close(self):
        self.client.close()