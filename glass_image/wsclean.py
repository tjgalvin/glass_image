"""Simple wrapper to run a typical glass wsclean imaging
"""
import os
from pathlib import Path

from spython import Client as sclient

from glass_image import WSCLEANDOCKER 
from glass_image.logging import logger
from glass_image.pointing import GPointing

def pull_wsclean_container() -> Path:
    """Download the docker image for wsclean

    Returns:
        Path: Path to the singularity container downloaded
    """
    logger.info(f"Downloading WSCLEAN docker image: {WSCLEANDOCKER}")

    sclient.load(sclient.load(WSCLEANDOCKER))
    sclient_path = Path(sclient.pull())
    
    logger.info(f"Downloaded container to {sclient_path=}")
    
    return sclient_path


def generate_wsclean_cmd(point: GPointing, round: int) -> str:
    
    forcemask = 6
    psfwindow = 75
    maskthresh = 10.
    size = 7500
    
    MS = f"{point.ms}"
    
    outname = f"{point.field}_fm{forcemask}_psfw{psfwindow}_mt{maskthresh}_r{round}"
    logger.debug(f"{outname=}")
    
    cmd = f"""wsclean \
    -abs-mem 100 \
    -mgain 0.70 \
    -force-mask-rounds ${forcemask} \
    -nmiter 15 \
    -niter 500000 \
    -local-rms \
    -auto-mask {maskthresh} \
    -local-rms-window {psfwindow} \
    -auto-threshold 1.0 \
    -name "{outname}" \
    -size {size} {size} \
    -scale "0.3asec" \
    -weight briggs 0.5 \
    -pol I \
    -use-wgridder \
    -join-channels \
    -channels-out 8 \
    -data-column DATA \
    -log-time \
    {MS}"""
    
    logger.debug(f"The wsclean command is \n {cmd}")
    
    return cmd


def run_wsclean_cmd(wsclean_img: Path, wsclean_cmd: str, binddir: Path = None) -> None:
    
    binddir = Path(os.getcwd()) if binddir is None else binddir
    binddir_str = str(binddir)

    logger.debug(f"Container {wsclean_img=}")
    logger.debug(f"Will bind to: {binddir_str}")
    logger.debug(f"Command to execute: {wsclean_cmd}")

    result = sclient.execute(
        image=wsclean_img,
        command=wsclean_cmd,
        bind=binddir_str,
        return_result=True
    )
    
    logger.debug(f"sclient result: {result}")
