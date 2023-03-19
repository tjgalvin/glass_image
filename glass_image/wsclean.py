"""Simple wrapper to run a typical glass wsclean imaging
"""
import os
from pathlib import Path
from typing import NamedTuple, Optional
from glob import glob

from spython.main import Client as sclient

from glass_image import WSCLEANDOCKER
from glass_image.logging import logger
from glass_image.pointing import Pointing


class WSCleanCMD(NamedTuple):
    cmd: str
    outname: str


class WSCleanOptions(NamedTuple):
    psfwindow: int = 65
    size: int = 5000
    forcemask: float = 6
    maskthresh: float = 7.5
    autothresh: float = 0.5


def image_round_options(img_round: int) -> WSCleanOptions:
    logger.debug(f"Obtainer wsclean image options")

    options = WSCleanOptions()

    if img_round == 1:
        options = WSCleanOptions(psfwindow=75, maskthresh=6.0)
    if img_round == 2:
        options = WSCleanOptions(psfwindow=85, maskthresh=5.0)
    if img_round == 3:
        options = WSCleanOptions(psfwindow=95, maskthresh=5.0)
    if img_round == 4:
        options = WSCleanOptions(psfwindow=105, maskthresh=5.0)
    if img_round >= 4:
        options = WSCleanOptions(psfwindow=105, maskthresh=3.0)

    logger.info(f"WSClean Options for round {img_round} are {options}")
    return options


def pull_wsclean_container() -> Path:
    """Download the docker image for wsclean

    Returns:
        Path: Path to the singularity container downloaded
    """
    logger.info(f"Downloading WSCLEAN docker image: {WSCLEANDOCKER}")

    sclient.load(WSCLEANDOCKER)
    sclient_path = Path(sclient.pull())

    logger.info(f"Downloaded container to {sclient_path=}")

    return sclient_path


def generate_wsclean_cmd(point: Pointing, img_round: int) -> WSCleanCMD:
    # Get the options for this round of imaging
    woptions = image_round_options(img_round=img_round)

    MS = f"{point.ms}"

    outname = (
        f"{point.field}_"
        f"fm{woptions.forcemask}_"
        f"psfw{woptions.psfwindow}_"
        f"mt{woptions.maskthresh}_"
        f"at{woptions.autothresh}_"
        f"round{img_round}"
    )
    logger.debug(f"{outname=}")

    cmd = f"""wsclean 
    -abs-mem 100 
    -mgain 0.70 
    -force-mask-rounds {woptions.forcemask} 
    -nmiter 15 
    -niter 500000 
    -local-rms 
    -auto-mask {woptions.maskthresh} 
    -local-rms-window {woptions.psfwindow} 
    -auto-threshold {woptions.autothresh} 
    -name {outname} 
    -size {woptions.size} {woptions.size} 
    -scale 0.3asec 
    -weight briggs 0.5 
    -pol I 
    -use-wgridder 
    -join-channels 
    -channels-out 16 
    -data-column DATA 
    {MS}"""

    cmd = " ".join([i.strip() for i in cmd.splitlines()])
    logger.debug(f"The wsclean command is \n {cmd}")

    wsclean_cmd = WSCleanCMD(cmd=cmd, outname=outname)

    return wsclean_cmd


def move_wsclean_out_into(dest_path: Path, outname: str) -> None:
    if not dest_path.exists():
        logger.info(f"Creating {dest_path}")
        dest_path.mkdir(parents=True)

    files = glob(f"{outname}*")
    logger.debug(f"Searched for files matching {outname}, found {len(files)}")

    for file in files:
        file_path = Path(file)
        logger.debug(f"Moving {file} into {str(dest_path)}")
        file_path.rename(dest_path / file_path.name)


def run_wsclean_cmd(
    wsclean_img: Path,
    wsclean_cmd: WSCleanCMD,
    binddir: Optional[Path] = None,
    move_into: Optional[Path] = None,
) -> None:
    binddir = Path(os.getcwd()) if binddir is None else binddir
    binddir_str = str(binddir)

    logger.debug(f"Container {wsclean_img=}")
    logger.debug(f"Will bind to: {binddir_str}")
    logger.debug(f"Command to execute: {wsclean_cmd.cmd}")

    result = sclient.execute(
        image=wsclean_img,
        command=wsclean_cmd.cmd,
        bind=binddir_str,
        return_result=True,
        stream=True,
    )

    for line in result:
        logger.info(line.rstrip())

    if move_into is not None:
        move_wsclean_out_into(move_into, wsclean_cmd.outname)
