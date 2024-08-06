"""lab_gen package."""

import sys

from loguru import logger


logger.remove()
logger.add(sys.stderr, format="{level}: {time:DD/MM/YY HH:mm:ss} | {name} | {message}")
