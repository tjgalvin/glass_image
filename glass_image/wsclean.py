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
from glass_image.image_utils import find_fits_mask
from glass_image.options import WSCleanCMD, WSCleanOptions


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
    """Construct a wsclean command to execute made against some image specification. 
    
    Args:
        point (Pointing): The measurement set to image
        options (WSCleanOptions): The imaging specifications
        
    Returns:
        WSCleanCMD: The `wsclean` command that will be executed. 
    """
    MS = f"{point.ms}"

    if options.fitsmask:
        fits_clean_mask = find_fits_mask(point=point)
        logger.info(f"Using FITS clean mask in {fits_clean_mask}")

        outname = (
            f"{point.field}_"
            f"psfw{options.psfwindow}_"
            f"fitscleanmask_"
            f"at{options.autothresh}_"
            f"round{options.round}"
        )
        mask_options = (
            f"-fits-mask {str(fits_clean_mask)} "
            f"-local-rms "
            f"-local-rms-window {options.psfwindow} "
        )
    else:
        outname = (
            f"{point.field}_"
            f"fm{options.forcemask}_"
            f"psfw{options.psfwindow}_"
            f"mt{options.maskthresh}_"
            f"at{options.autothresh}_"
            f"round{options.round}"
        )
        mask_options = (
            f"-force-mask-rounds {options.forcemask} "
            f"-local-rms "
            f"-auto-mask {options.maskthresh} "
            f"-local-rms-window {options.psfwindow} "
        )

    if options.multiscale:
        multiscale = (
            f"-multiscale " f"-multiscale-scale-bias {options.multiscale_scale_bias} "
        )
    else:
        multiscale = ""

    logger.debug(f"{outname=}")
    logger.debug(f"{mask_options}")

    cmd = f"""wsclean 
    -abs-mem {options.absmem} 
    -mgain {options.mgain}      
    {mask_options} 
    -nmiter {options.nmiter} 
    -niter {options.niter} 
    -auto-threshold {options.autothresh} 
    -name {outname} 
    -size {options.size} {options.size} 
    -scale 0.3asec 
    -weight briggs 0.5 
    -pol I 
    -use-wgridder 
    -join-channels 
    {multiscale}
    -channels-out {options.channels_out} 
    -fit-spectral-pol {options.fit_spectral_pol}
    -data-column DATA 
    {MS}"""

    cmd = " ".join([i.strip() for i in cmd.splitlines()])
    logger.debug(f"The wsclean command is \n {cmd}")

    wsclean_cmd = WSCleanCMD(cmd=cmd, outname=outname)

    return wsclean_cmd


def move_wsclean_out_into(dest_path: Path, outname: str) -> None:
    """Move a set of files produced by wsclean into a output directory. 
    A glob expression based on the provided `outname` is used to 
    identify files that will be moved. 
    
    If the `outname` is correctly formed, files include the dirty maps, 
    synthesised PSFs, clean models and restored images. 

    Args:
        dest_path (Path): The directory to move files into
        outname (str): Component of the filename to glob against. 
    """
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
    """Execute a `WSCleanCMD` string within the context of a wsclean singularity container. 
    Output produced by `wsclean` will be streamed to the stderr. 

    Args:
        wsclean_img (Path): Path to the singularity image container wsclean
        wsclean_cmd (WSCleanCMD): The processed wsclean command that will be executed
        binddir (Optional[Path], optional): Additional directories to include in the singularity bindpath. Defaults to None.
        move_into (Optional[Path], optional): Directory location to move files into. Defaults to None.
        clean_up (bool, optional): Will delete 'unnecessary' files, including the dirty maps and PSFs. This is primarily intended to conserve disk space. Defaults to True.
    """
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
            # + list(work_dir.glob(f"{wsclean_cmd.outname}*residual.fits"))
        )

    if move_into is not None:
        move_wsclean_out_into(move_into, wsclean_cmd.outname)


def generate_wsclean_header(wsclean_img: Path, point: Pointing,options: WSCleanOptions,binddir: Optional[Path] = None) -> fits.header.Header:
    """Will return a generice FITS header that would be expected from a genuine `wsclean` image. Internally
    a `wsclean` command is executed to generate a image with no cleaning. The header is extracted and returned
    after the image products are delected. 
    
    Args:
        wsclean_img (Path): Path to the singularity image that contains wsclean
        point (Pointing): Measurement set to image to extract the header from
        options (WSCleanOptions): Imaging specification to use. This should be the same as the intended final image. 
        binddir (Path, optional): Additional directories to bind to. Defaults ot None. 
        
    Returns:
        fits.header.Header: The extracted FITS header to be expected from `wsclean` produced images. 
    """ 
    
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
