# Telemetry Agent

A lightweight network telemetry collector that runs `ping` and `traceroute` against one (or more) targets, parses the results with `jc`, normalizes them into Python dataclasses, and optionally writes the data to a time‑series database. The goal is to keep the service simple, observable, and easy to validate in both local and containerized environments.

---

## Requirements

To run the telemetry agent locally or in Docker, you’ll need the following:

### Runtime
- **Python 3.10 (or greater)+**
  - Required for running the agent directly from the command line.
  - Install dependencies with `pip install -r requirements.txt`.

- **Docker (optional)**
  - Used for containerized execution.
  - Docker Compose is recommended if you want to run the agent alongside a database and with a Grafana dashboard.

### System Utilities
The agent relies on system‑level networking tools:

- `ping`
- `traceroute`

These are available by default on most Linux and macOS systems.  
On Windows, you may need to install or enable `tracert`/`traceroute` equivalents or run inside WSL/Docker.

### Optional (for database writes)
If you plan to write telemetry to a time‑series database:

- **InfluxDB 2.x or compatible endpoint**
- A valid **API token**
- Environment variables configured in `.env`:
  - `INFLUXDB_URL`
  - `INFLUXDB_TOKEN`
  - `INFLUXDB_ORG`
  - `INFLUXDB_BUCKET`

These are not required when running with `--no-db`.

### Recommended Tools
- `jc` (installed via `pip`) for parsing ping/traceroute output
- `pytest` (optional) if you add tests later

---

## Features

- Executes `ping` and `traceroute` using system utilities  
- Parses output through `jc` for consistent JSON structures  
- Converts raw data into typed Python models  
- Assembles a unified `Telemetry` object  
- Optional database writer (InfluxDB or similar)  
- Structured logging throughout the pipeline  
- CLI flags for local validation (`--target`, `--no-db`)  
- Environment‑driven configuration for Docker deployments  

---

## Architecture Overview

main.py  →  collectors/  →  parsers/ →  converters/  →  Telemetry model  →  DB writer (optional)

- main.py: CLI entrypoint, loop, DB and target arguments for running outside of Docker
- collectors: Runs ping/traceroute and captures output
- parsers: Parse the ping/traceroute data using jc
- converters: Normalizes jc output into dataclasses
- Telemetry: Final structured result
- DB writer: Optional persistence layer

---

## Installation

### Python environment (outside of Docker)

```
python3.14 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r agent/requirements.txt
```

### Docker
```
docker compose up --build -d
```

---

## Running the Agent

### Option A - Local run (no database required)
```
# Create virtual environment
python3.14 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r agent/requirements.txt

# Execute agent
python3.14 -m agent.main --target <target> --no-db # required if not using Docker to run the database instance
```
You’ll see logs for:

- ping execution
- traceroute execution
- geolocation execution
- jc parsing
- converter output
- final Telemetry object

This mode is ideal for validating the service without using a database.

### Option B - Using environment variables
```
TARGETS=target-name(s)  # If specifying multiple targets, separate with comma
python -m agent.main --targets=<targets> --no-db
```

Target resolution follows this order:
- --targets flag
- TARGETS environment variable
- Error will be raised if neither is provided

### Option C - With database writes enabled (NOTE: Must use Docker)

- Copy the .env.example file to .env, this file contains the environment variables to be used
- Specify target hostname in the .env file.  Other values can be updated to suit needs, although care should be taken to ensure that the agent still runs properly.
- Build the Docker image for the telemetry agent
- Confirm that the name of the Docker image also noted in the telemetry agent as specified in the docker-compose.yml file
- Start the Docker containers using the below command:
```
docker compose up --build -d
```

---

## Accessing InfluxDB and Grafana
If you're running the stack using Docker Compose, both InfluxDB and Grafana are exposed on local ports so you can inspect telemetry data visually.

### InfluxDB
InfluxDB is available at:

```
http://localhost:8086
```

Default credentials (if using the standard InfluxDB setup):

- Username: Provided in your .env file as INFLUXDB_USER
- Password: Provided in your .env file as INFLUXDB_PASSWORD
- Token: Provided in your .env file as INFLUXDB_TOKEN

Once logged in, you can:

- View the bucket you configured (e.g., telemetry)
- Explore data using the InfluxDB Data Explorer
- Run Flux queries to inspect ping/traceroute metrics
- Verify that the agent is writing data correctly (unless running with --no-db)

### Grafana
Grafana is available at:

```
http://localhost:3000
```

NOTE: The Grafana Docker container runs as root so that the datasource can be dynamically created with the InfluxDB token.  Future update to determine if this token can be written without root access to the Grafana container.

Default credentials (Grafana defaults):

- Username: admin
- Password: admin (You’ll be prompted to change this on first login.)

Once inside Grafana, you can:

- Access the dashboard with the telemetry (Telemetry Agent Dashboard)
- From menu, go to 'Dashboards', and choose 'telemetry Agent Dashboard'

### Docker Compose Networking Notes
If you're using Docker Compose:

Services can reach each other by container name (influxdb, grafana, agent)

The agent writes to InfluxDB using the internal URL:

```
http://influxdb:8086
```

Your browser accesses them via localhost because ports are mapped:

```
influxdb:8086 → localhost:8086
grafana:3000  → localhost:3000
```

### Verifying Data Flow
To confirm everything is working:

Start the stack:

```
docker compose up --build -d
```

Run the agent (inside Docker or locally):

```
python -m agent.main --target target-name
```

- Open InfluxDB → Data Explorer → Query your bucket
- Open Grafana → Build or view dashboards
- Confirm telemetry points appear as the agent runs
- This gives reviewers a clear, visual way to validate the service beyond logs.

---

## Validation Guide
The assessment requires tests OR a way to validate the service works properly, along with logging. This project focuses on a clear, practical validation workflow:

### Structured logging
Every stage logs what it’s doing, including:

- subprocess calls
- jc parsing
- converter normalization
- telemetry assembly
- DB write attempts (or skips)

In production, the agent runs in a Docker container and logs to stdout only, and if the logs need to be stored in a file, this could be implemented separately.  For local development and testing purposes using python, the logs are written to stdout and file.

### Local validation mode (--no-db)
Allows full end‑to‑end validation without needing credentials.

### CLI‑driven target selection (--target)
Makes it easy to test different hosts.

### Deterministic behavior
The converters and collectors produce predictable, structured output that’s easy to inspect in logs.

This approach keeps the project straightforward and easy to verify within the assessment timeline.

---

## Design Decisions and Rationale
This project was built to be easy to adopt, run, and enhance in a production environment.  There were a few key decisions that shaped the implementation, including:

- Using system utilities (ping, traceroute)
These tools are widely available and perform the same functions across all implementations.  Note that when used in a Docker container, output will vary depending on the host operating system, and as such, Linux-based OSes are preferred for best results.
- Parsing with JSON Convert (jc)
This tool specifically provides custom parsers to output ping and traceroute results into an easily digestible JSON format that can be used by the telmeetry agent, and saved on having to create custom parsers to perform the same task.
- Organizing by function
Creating dedicated files specific to ping, traceroute, and command runner for easier management/maintenance in future versions.
- Service Validation Feature
The asssessment requirements stated to provide a way to validate the service and/or tests to validate the telemetry agent works properly.  A full testing suite is planned as a future enhancement.
- Telemetry metatadata collection
The initial version 

---

## Geolocaton bonus feature
The agent includes an optional geolocation collector that enriches telemetry with IP‑based location data. This uses the public IPWhois API:

```
https://ipwhois.app/json/<IP_ADDRESS>
```

The collector retrieves:
- city
- region
- country
- latitude/longitude
- ISP
- ASN (if available)

This data is normalized into a GeoLocation dataclass and included in the final Telemetry object. The feature is lightweight, requires no authentication, and integrates cleanly with the existing collector → converter → telemetry pipeline.

Note that the geolocation data is cached, to improve performance and ensure quotas to free geolocation services are not exceeded which would hinder the performance of the agent.

--- 
## Tests (Future Enhancement)
Automated tests are not included in this submission. Given the one‑week assessment window, the focus was on delivering:

- a working telemetry pipeline
- a simple validation workflow, along with logging
- predictable behavior in both local and containerized environments

A test suite (converters, collectors, and telemetry assembly) is planned as a future enhancement and can be added before the reviewer walkthrough.

---

## Design Notes

- Converters and collectors are intentionally simple and predictable.
- DB writes are optional and skipped when disabled.
- Logging is included and accessible via the host (if run locally, file is named telemetry-agent.log) or from within the Docker container (via "docker logs telemetry-agent -f")
- CLI flags make the service easy to validate in any environment.
- The code is structured to make future testing straightforward.

---

## Example Output

```
2025-12-22 17:01:25,324 - telemetry-agent - INFO - Running telemetry collection for target: target-name
2025-12-22 17:01:25,324 - telemetry-agent - INFO - DB writes disabled: False
2025-12-22 17:01:25,324 - telemetry-agent - INFO - Using token from InfluxDB config file.
2025-12-22 17:01:25,339 - telemetry-agent - INFO - Collecting telemetry data for target: target-name
2025-12-22 17:01:25,339 - telemetry-agent - INFO - Running ping for host: target-name
2025-12-22 17:01:25,339 - telemetry-agent - INFO - Executing command: ping -c 4 target-name
2025-12-22 17:01:28,369 - telemetry-agent - INFO - Running traceroute for host: target-name
2025-12-22 17:01:28,369 - telemetry-agent - INFO - Executing command: traceroute target-name 2>&1
2025-12-22 13:03:44,441 - telemetry-agent - INFO - Collecting geolocation data for: target-name
2025-12-22 17:01:58,510 - telemetry-agent - INFO - Wrote telemetry data for target-name to InfluxDB.
2025-12-22 17:01:58,510 - telemetry-agent - INFO - Sleeping for 60 seconds before next collection.
```

---

## Future Improvements

- Add automated tests for converters, collectors, and telmeetry assembly
- Add features to allow for better scaling, including concurrency and high availability
- Implement parallel collection to increase speed and efficiency
- Implement two-factor authentication (2FA)
- Integrate geolocation data to map network flow between the source and target locations
- Parse hop list and create Grafana dashboard to show route taken from source to target
