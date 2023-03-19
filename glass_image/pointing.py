"""Container object to hold a measurement set information
"""

from typing import NamedTuple
from pathlib import Path


class Pointing(NamedTuple):
    workdir: Path
    field: str
    ms: Path
