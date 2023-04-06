"""Location for all Option sytle classes
"""

from typing import NamedTuple

class ImagerOptions(NamedTuple):
    rounds: int = 5
    clean_up: bool = False

class WSCleanCMD(NamedTuple):
    cmd: str
    outname: str

class WSCleanOptions(NamedTuple):
    absmem: int = 100
    psfwindow: int = 65
    size: int = 7000
    forcemask: float = 10
    maskthresh: float = 5
    autothresh: float = 0.5
    channels_out: int = 8
    round: int = 0
    mgain: float = 0.7
    fitsmask: bool = False
    nmiter: int = 15
    niter: int = 50000
    multiscale: bool = False
    multiscale_scale_bias: float = 0.9
    fit_spectral_pol: int = 4
    robust: int = 0.5

class CasaSCOptions(NamedTuple):
    solint: str = "60s"
    nspw: int = 4
    calmode: str = "p"
    round: int = 0

class ImageRoundOptions(NamedTuple):
    wsclean: WSCleanOptions
    casasc: CasaSCOptions
