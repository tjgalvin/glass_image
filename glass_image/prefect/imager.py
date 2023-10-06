"""A prefect based pipeline for the imaging of GLASS data
"""
import logging
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional, List

from prefect import flow, task

from glass_image.logging import logger
from glass_image.glass_imager import image_round, image_cband, unmapped
from glass_image.prefect.cluster import get_dask_runner

task_image_cband = task(image_cband)


@flow
def imaging_pipeline(
    mss: List[Path],
    imager_config: Path,
    workdir: Optional[Path] = None,
    wsclean_img: Optional[Path] = None,
    clean_up: bool = True,
):
    logger.info(f"Will attempt to run the pipeline against {len(mss)}.")
    logger.info(f"Inputs: ")
    logger.info(f"{imager_config=}")
    logger.info(f"{workdir=}")
    logger.info(f"{wsclean_img=}")
    logger.info(f"{clean_up=}")

    task_image_cband.map(
        ms_path=mss,
        imager_config=unmapped(imager_config),
        workdir=unmapped(workdir),
        wsclean_img=unmapped(wsclean_img),
    )


def get_parser():
    parser = ArgumentParser(description="A simple imaging script for GLASS data")

    parser.add_argument(
        "cluster_config", type=Path, help="Path to the cluster configuration to use"
    )
    parser.add_argument("ms", type=Path, help="Path to the field to image", nargs="+")

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
        "imager_config",
        type=Path,
        default=None,
        help="A glass_image style yaml configuration file to adjust options and self-cal settings. This is intended to hold strictly configurables related to imaging and self-calibration, not configurables about the main program (e.g. work directory)",
    )

    return parser


def cli():
    parser = get_parser()

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    dask_task_funner = get_dask_runner(cluster=args.cluster_config)

    imaging_pipeline.with_options(task_runner=dask_task_funner)(
        mss=args.ms,
        imager_config=args.imager_config,
        workdir=args.workdir,
        wsclean_img=args.wsclean_img,
    )


if __name__ == "__main__":
    cli()
