"""The main script runner for GLASS imager
"""
import os
import logging
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional, NamedTuple

from glass_image import WSCLEANDOCKER
from glass_image.wsclean import (
    pull_wsclean_container,
    generate_wsclean_cmd,
    run_wsclean_cmd,
    WSCleanOptions,
)
from glass_image.logging import logger
from glass_image.pointing import Pointing
from glass_image.casa_selfcal import derive_apply_selfcal
from glass_image.configuration import ImageRoundOptions, get_imager_options, get_round_options


class ImagerOptions(NamedTuple):
    rounds: int = 5


def image_round(
    wsclean_img: Path,
    point: Pointing,
    img_round: int = 0,
    wsclean_options: Optional[WSCleanOptions] = None,
    clean_up: bool = True,
) -> None:
    logger.info(f"Will be imaging {point}")
    logger.info(f"Using container: {wsclean_img=}")

    wsclean_cmd = generate_wsclean_cmd(
        point=point, img_round=img_round, options=wsclean_options
    )

    output_dir = Path(f"round_{img_round}") if img_round > 0 else Path("no_selfcal")
    assert not output_dir.exists(), f"Output folder {output_dir} already exists. "

    run_wsclean_cmd(
        wsclean_img=wsclean_img,
        wsclean_cmd=wsclean_cmd,
        move_into=output_dir,
        clean_up=clean_up,
    )


def image_cband(
    ms_path: Path,
    workdir: Optional[Path] = None,
    wsclean_img: Optional[Path] = None,
    imager_config: Optional[Path] = None,
    clean_up: bool = True,
) -> None:
    assert ms_path.exists(), f"MS {ms_path} does not exist"

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
    if isinstance(imager_config, Path):
        imager_options = ImagerOptions(**get_imager_options(imager_config))
    else:
        imager_options = ImagerOptions()
    

    img_round_options = ImageRoundOptions()
    if isinstance(imager_config, Path):
        img_round_options = get_round_options(imager_config, img_round=0)

    image_round(
        wsclean_img=wsclean_img, point=point, wsclean_options=img_round_options.wsclean
    )

    for img_round in range(1, imager_options.rounds):
        img_round_options = ImageRoundOptions()
        if isinstance(imager_config, Path):
            logger.info(f"Getting options from {imager_config} in {img_round}")
            img_round_options = get_round_options(imager_config, img_round=img_round)
        
        logger.info(f"\n\nAttempting selcalibration for round {img_round}")
        selfcal_point = derive_apply_selfcal(
            in_point=point, img_round=img_round, options=img_round_options.casasc
        )

        logger.info(f"\n\nRunning imaging for round {img_round}")
        image_round(
            wsclean_img=wsclean_img,
            point=selfcal_point,
            img_round=img_round,
            wsclean_options=img_round_options.wsclean,
            clean_up=clean_up,
        )

        logger.info(f"\n\nUpdating current MS from {point.ms} to {selfcal_point.ms}")
        point = selfcal_point


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(description="A simple imaging script for GLASS data")

    parser.add_argument("ms", type=Path, help="Path to the field to image")
    parser.add_argument(
        "-w",
        "--workdir",
        type=Path,
        default=None,
        help="Where to carry out the processing",
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
    parser.add_argument(
        "-i",
        "--imager-config",
        type=Path,
        default=None,
        help="A glass_image style yaml configuration file to adjust options and self-cal settings. This is intended to hold strictly configurables related to imaging and self-calibration, not configurables about the main program (e.g. work directory)",
    )

    return parser


def cli() -> None:
    parser = get_parser()

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    image_cband(
        ms_path=args.ms,
        workdir=args.workdir,
        wsclean_img=args.wsclean_image,
        imager_config=args.imager_config,
    )


if __name__ == "__main__":
    cli()
