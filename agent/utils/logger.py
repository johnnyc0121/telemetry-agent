import logging
import os


def running_in_docker():
    return os.path.exists('/.dockerenv')

def setup_logging():
    logger = logging.getLogger("telemetry-agent")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger  # Logger already configured

    # Configure the logging formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Always log to console / stdout
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Only log to file if NOT running in a Docker container
    if not running_in_docker():
        file_handler = logging.FileHandler("telemetry-agent.log")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
