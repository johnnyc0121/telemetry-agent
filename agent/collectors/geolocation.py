import os
import requests
import socket
import logging

from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("telemetry-agent")

# Module level caches
_resolved_ips = {}
_geo_cache = {}

@dataclass
class GeoLocation:
    ip: str
    city: Optional[str]
    region: Optional[str]
    country: Optional[str]
    latitude: Optional[str]
    longitude: Optional[str]
    isp: Optional[str]


def resolve_target(target):
    # Check if target has already been resolved, to reduce DNS name resolution lookups
    if target in _resolved_ips:
        logger.info(f"{target} -- Using cached DNS name resolution for IP address")
        ip = _resolved_ips[target]
        return ip

    # Resolve if not done already
    try:
        logger.info(f"{target} -- Collecting IP via DNS name resolution")
        ip = socket.gethostbyname(target)
        _resolved_ips[target] = ip
        return ip
    except socket.gaierror as e:
        logger.error(f"{target} -- DNS name does not resolve to IP")
        return None

def convert_geolocation_dict(geo_data: dict) -> GeoLocation:
    if not isinstance(geo_data, dict) or not geo_data:
        return None

    return GeoLocation(
        ip=geo_data.get("ip", ""), 
        city=geo_data.get("city"), 
        region=geo_data.get("region"), 
        country=geo_data.get("country"), 
        latitude=float(geo_data["lat"]) if geo_data.get("lat") else None, 
        longitude=float(geo_data["lon"]) if geo_data.get("lon") else None, 
        isp=geo_data.get("isp")
    )

def collect_geolocation_data(target: str, timeout: float = 5.0) -> dict:
    # Declare the geolocation API URL
    geolocation_api_url = os.getenv("GEOLOCATION_API_URL", "http://ip-api.com/json")

    # Resolve target to an IP address
    ip = resolve_target(target)
    if ip is None:
        return None

    # Check if IP is already in the geocache object, else collect the geolocation data
    if ip in _geo_cache:
        logger.info(f"{target} -- Using cached geolocation for {ip}")
        geo_data = _geo_cache[ip]

    else:
        url = f"{geolocation_api_url}/{ip}"
        logger.info(f"{target} -- Collecting geolocation data from: {url}")
        logger.info(f"{target} -- Collecting geolocation data for: {ip}")

        try:
            response = requests.get(url, timeout = timeout)
            response.raise_for_status()
            geo_data = response.json()

            # Store data in the cache in case it's needed again
            _geo_cache[ip] = geo_data

        except Exception as e:
            logger.error(f"{target} -- Failed to collect geolocation data: {e}")
            return None

    # Use for debugging purposes
    # logger.info(f"Raw geolocation data")
    # logger.info("--------------------------")
    # logger.info(geo_data)

    return convert_geolocation_dict(geo_data)
