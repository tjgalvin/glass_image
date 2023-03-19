"""Utility functions to help with processing
"""
import subprocess

from glass_image.logging import logger


def call(*args, **kwargs):
    """Wrapper for subprocess.Popen to log the command and output
    All arguments are passed to subprocess.Popen
    """
    # Call a subprocess, print the command to stdout
    logger.info(" ".join(args[0]))
    process = subprocess.Popen(
        *args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kwargs
    )

    with process.stdout:
        try:
            for line in iter(process.stdout.readline, b""):
                logger.info(line.decode("utf-8").strip())

        except subprocess.CalledProcessError as e:
            logger.error(f"{str(e)}")
