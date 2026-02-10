import logging
import subprocess
import sys

logger = logging.getLogger("telemetry-agent")


def run_command(target: str, command: str, args: str):
    """Run a shell command and return the output."""
    logger.info(f"{target} -- Executing command: {command} {args}")

    try:
        result = subprocess.run(f"{command} {args}", shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            logger.error(f"{target} -- Error running command {command}: {result.stderr}")
            return None

    except Exception as e:
        logger.error(f"{target} -- Exception occurred while running command {command}: {e}")
        return None

    return result.stdout
