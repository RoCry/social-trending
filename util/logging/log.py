import logging
import os

# Configure logging
logger = logging.getLogger("social-trending")
logger.setLevel(os.environ.get("LOGLEVEL", "INFO"))

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - [%(name)s] %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
