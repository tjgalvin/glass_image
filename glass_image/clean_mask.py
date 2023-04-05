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


from glass_image import WSCLEANDOCKER
from glass_image.logging import logger
from glass_image.pointing import Pointing
from glass_image.configuration import get_round_options
from glass_image.wsclean import pull_wsclean_container, generate_wsclean_header
from glass_image.image_utils import cutout_mask

def create_clean_mask(
    ms_path: Path,
    imager_config: Path,
    mosaic_mask: Path,
    wsclean_img: Optional[Path] = None,
    workdir: Optional[Path] = None,
) -> None:
    """Extract a clean mask for a pointing from a larger masked image. Idea being to image
    the GLASS pointings individually, co-added to get optimal sensitivity, and then create
    a mask of pixels about some signal-to-noise cut (this last stage is outside the scope
    of this function). 
    
    Once this mask has been extracted then it may be supplied to wsclean. This might enable
    wsclean to clean a lot more aggressively with less worry of cleaning suprious sources. 
    
    A dummy FITS header which contains the WSC to extract upon by creating a dirty 
    image with wsclean with representative options. 

    Args:
        ms_path (Path): The measurement set that a clean mask will be extracted for
        imager_config (Path): WSClean imaging settings. These need to be representative of those in the deep clean
        mosaic_mask (Path): Path to the mask of the deep co-added image
        wsclean_img (Optional[Path], optional): Path to singularity image containing wsclean. Defaults to None.
        workdir (Optional[Path], optional): The directory where work will be carried out. Defaults to None.
    """
    assert ms_path.exists(), f"MS {ms_path} does not exist"
    assert (
        imager_config.exists()
    ), f"Imager configuration {imager_config} does not exist"

    if workdir is None:
        workdir = Path(ms_path.parent)

    logger.info(f"Changing directory to: {workdir}")
    os.chdir(workdir)

    logger.debug(f"Input MS: {ms_path}")
    name_comps = ms_path.name.split(".")
    logger.debug(f"{name_comps}")
    field = "_".join(name_comps[:1])

    point = Pointing(workdir=workdir, field=field, ms=Path(ms_path.name))

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
    """Return a generic argurment parser for the clean mask task

    Returns:
        ArgumentParser: Argument parser with options populated
    """
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
    """CLI entry point for clean mask
    """
    parser = get_parser()

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    create_clean_mask(args.ms, args.imager_config.absolute(), args.mask, wsclean_img=args.wsclean_image)


if __name__ == "__main__":
    cli()
