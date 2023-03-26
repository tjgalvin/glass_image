"""Simple wrapper to run a typical glass wsclean imaging
"""
import os
from pathlib import Path
from typing import NamedTuple, Optional
from glob import glob

from spython.main import Client as sclient
from astropy.io import fits

from glass_image import WSCLEANDOCKER
from glass_image.logging import logger
from glass_image.pointing import Pointing
from glass_image.utils import remove_files_folders


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


def generate_wsclean_cmd(
    point: Pointing,
    options: WSCleanOptions,
) -> WSCleanCMD:
    MS = f"{point.ms}"

    outname = (
        f"{point.field}_"
        f"fm{options.forcemask}_"
        f"psfw{options.psfwindow}_"
        f"mt{options.maskthresh}_"
        f"at{options.autothresh}_"
        f"round{options.round}"
    )
    logger.debug(f"{outname=}")

    cmd = f"""wsclean 
    -abs-mem {options.absmem} 
    -mgain {options.mgain} 
    -force-mask-rounds {options.forcemask} 
    -nmiter 15 
    -niter 500000 
    -local-rms 
    -auto-mask {options.maskthresh} 
    -local-rms-window {options.psfwindow} 
    -auto-threshold {options.autothresh} 
    -name {outname} 
    -size {options.size} {options.size} 
    -scale 0.3asec 
    -weight briggs 0.5 
    -pol I 
    -use-wgridder 
    -join-channels 
    -channels-out {options.channels_out} 
    -multiscale
    -multiscale-scale-bias 0.6
    -fit-spectral-pol 3
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
    clean_up: bool = True,
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

    # Streaming the output from the singularity command
    for line in result:
        logger.info(line.rstrip())

    # Cleanup to save space
    if clean_up:
        work_dir = Path(os.getcwd())
        remove_files_folders(
            list(work_dir.glob(f"{wsclean_cmd.outname}*dirty.fits"))
            + list(work_dir.glob(f"{wsclean_cmd.outname}*psf.fits"))
            + list(work_dir.glob(f"{wsclean_cmd.outname}*residual.fits"))
        )

    if move_into is not None:
        move_wsclean_out_into(move_into, wsclean_cmd.outname)


def generate_wsclean_header(
    wsclean_img: Path,
    point: Pointing,
    options: WSCleanOptions,
    binddir: Optional[Path] = None,
) -> fits.header.Header:
    MS = point.ms
    logger.info(f"Generating a dirty map for wsclean {point.ms}. ")

    binddir = Path(os.getcwd()) if binddir is None else binddir
    binddir_str = str(binddir)

    outname = f"{point.field}_" f"round{options.round}_" "mask"

    cmd = f"""wsclean 
    -abs-mem {options.absmem} 
    -mgain 1.0
    -nmiter 1 
    -niter 0 
    -name {outname} 
    -size {options.size} {options.size} 
    -scale 0.3asec 
    -weight briggs 0.5 
    -pol XX 
    -use-wgridder 
    -join-channels 
    -channels-out {options.channels_out} 
    -data-column DATA 
    {MS}"""

    cmd = " ".join([i.strip() for i in cmd.splitlines()])
    logger.debug(f"The wsclean command is \n {cmd}")

    logger.info(f"Constructed out name if {outname}")
    logger.debug(f"Dirty wsclean command is {cmd}")

    result = sclient.execute(
        image=wsclean_img,
        command=cmd,
        bind=binddir_str,
        return_result=True,
        stream=True,
    )

    # Streaming the output from the singularity command
    for line in result:
        logger.info(line.rstrip())

    work_dir = Path(os.getcwd())

    image_header = fits.getheader(f"{outname}-MFS-image.fits")

    remove_files_folders(
        list(work_dir.glob(f"{outname}-00??*fits"))
        + list(work_dir.glob(f"{outname}-MFS-*.fits"))
    )

    logger.debug(f"Imager header is {type(image_header)}")

    return image_header
