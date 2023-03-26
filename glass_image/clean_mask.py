"""Cutout a clean mask from a larger clean mask. This larger clean
mask would be derived from a complete co-add. The clean mask derived
from the co-added image should be deeper and more robust against aretfact
that may be present in individual images. 
"""
import os
import logging
from pathlib import Path
from argparse import ArgumentParser
from typing import Optional

import numpy as np
from astropy.wcs import WCS
from astropy.io import fits
from astropy.nddata.utils import Cutout2D
from reproject import reproject_interp

from glass_image import WSCLEANDOCKER
from glass_image.logging import logger
from glass_image.pointing import Pointing
from glass_image.configuration import get_imager_options, get_round_options
from glass_image.wsclean import pull_wsclean_container, generate_wsclean_header
from glass_image.configuration import ImageRoundOptions
from glass_image.errors import FITSCleanMaskNotFound

def find_fits_mask(point: Pointing) -> Path:
    """Searches and returns the Path to the clean mask. The initial signal-cut
    mask is intended to be produced from the larger mosaic co-add of all data. 
    This FITS clean mask is to be an extract of the larger mosaic, where the region
    corresponds to the region being imaged. 

    Args:
        point (Pointing): Measurement set pointing details that the FITS clean mask corresponds to

    Returns:
        Path: Path to the generated clean ask
    """
    out_path = Path(f"{point.field}_clean_mask.fits")

    if not out_path.exists():
        raise FITSCleanMaskNotFound(out_path)
    
    return out_path

def cutout_mask(image_header: fits.header.Header, mosaic_mask: Path, point: Pointing, options: ImageRoundOptions) -> Path:
    logger.info(f"Will be extracting clean mask from {mosaic_mask}")
    
    img_npix = options.wsclean.size
    img_shape = (img_npix, img_npix)
    
    logger.debug(f"Output shape is {img_shape}")
    
    with fits.open(str(mosaic_mask)) as mask_fits:
        extract_img = reproject_interp(
                (np.squeeze(mask_fits[0].data), WCS(mask_fits[0].header).celestial),
                WCS(image_header).celestial,
                shape_out=img_shape
        )
    
    logger.info(f"Extracted image header {extract_img}")
    
    out_path = Path(f"{point.field}_clean_mask.fits")
    fits.writeto(
        str(out_path),
        extract_img[0],
        image_header,
        overwrite=True
    )

    return out_path
    
    
def create_clean_mask(
    ms_path: Path,
    imager_config: Path,
    mosaic_mask: Path,
    wsclean_img: Optional[Path] = None,
    workdir: Optional[Path] = None,
) -> None:
    assert ms_path.exists(), f"MS {ms_path} does not exist"
    assert (
        imager_config.exists()
    ), f"Imager configuration {imager_config} does not exist"

    if workdir is not None:
        logger.info(f"Changing directory to: {workdir}")
        os.chdir(workdir)
    else:
        workdir = Path(os.getcwd())

    logger.debug(f"Input MS: {ms_path}")
    name_comps = ms_path.name.split(".")
    logger.debug(f"{name_comps}")
    field = "_".join(name_comps[:1])

    point = Pointing(workdir=workdir, field=field, ms=ms_path)

    if wsclean_img is None:
        logger.info("No wsclean-image provided. Will attempt to download. ")
        wsclean_img = pull_wsclean_container()

    logger.info(f"Formed point: {point}")
    logger.info(f"WSClean image: {wsclean_img}")

    logger.debug(f"Getting Imager related options.")

    img_round_options = get_round_options(imager_config, img_round=0)

    image_header = generate_wsclean_header(
        wsclean_img=wsclean_img, point=point, options=img_round_options.wsclean
    )
    cutout_mask(image_header=image_header, mosaic_mask=mosaic_mask, point=point, options=img_round_options)


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Extract a clean mask to use from a larger mosaic"
    )

    parser.add_argument(
        "ms", type=Path, help="The measurement ment set that will be used"
    )
    parser.add_argument(
        "imager_config", type=Path, help="The image configuration to use"
    )
    parser.add_argument(
        "mask", type=Path, help="Path to clean mask imager derived from coadded image"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--wsclean-image",
        type=Path,
        default=None,
        help=f"Path to the wsclean singularity container. If not provided will attempt to download {WSCLEANDOCKER}, a slightly modified wsclean image. ",
    )

    return parser


def cli() -> None:
    parser = get_parser()

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    create_clean_mask(args.ms, args.imager_config, args.mask, wsclean_img=args.wsclean_image)


if __name__ == "__main__":
    cli()
