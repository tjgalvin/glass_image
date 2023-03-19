"""Logging utilities for the glass_image operations
"""

import logging

# Create logger
logging.captureWarnings(True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

logger.addHandler(logging.StreamHandler())
