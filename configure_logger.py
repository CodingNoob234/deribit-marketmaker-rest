import logging
from config import config_dict

def configure_logger():
    # Map log level names to their corresponding constants
    log_level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    # Fetch the log level from environment variables
    log_level = config_dict.get("logging_level", "INFO").upper()

    # Set the log level to the corresponding constant from the mapping, or use INFO as the default
    log_level = log_level_mapping.get(log_level, logging.INFO)

    # Configure the logger with the specified log level and other settings
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )