"""Container object to hold a measurement set information
"""

from typing import NamedTuple
from pathlib import Path 


class GPointing(NamedTuple):
    workdir: Path
    field: str
    ms: str
    
