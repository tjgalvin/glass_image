"""Logging utilities for the glass_image operations
"""

import logging

# Create logger
logging.captureWarnings(True)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.WARNING)
