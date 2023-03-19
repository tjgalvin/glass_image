"""Utilities to convert the miriad visibility data into a measurement set
"""
import shutil
import logging
from pathlib import Path
from argparse import ArgumentParser
from typing import Optional

from casatasks import importuvfits

from glass_image.logging import logger
from glass_image.utils import ensure_dir_exists, call


def extract_field_name(miriad_vis: Path) -> str:
    logger.info(f"Extracting field name from {miriad_vis}")
    name = miriad_vis.name.split(".")[0]

    logger.info(f"Field name extracted {name}")

    return name


def convert_miriad_to_ms(
    miriad_vis: Path,
    output_dir: Path,
    clean_up: bool = True,
    field_out: bool = False,
    field_name: Optional[str] = None,
) -> Path:
    # will raise error when does not exist
    ensure_dir_exists(miriad_vis)

    if field_out:
        if field_name is None:
            field_name = extract_field_name(miriad_vis)

        output_dir = output_dir / field_name

    logger.info(f"Outputs will be writted to {output_dir}")
    if not output_dir.exists():
        logger.info(f"Creating output folder {output_dir}")
        output_dir.mkdir(parents=True)

    logger.info("Running avaver")
    uvaver_out = output_dir / miriad_vis.name
    call([f"uvaver", f"vis='{str(miriad_vis)}'", f"out='{str(uvaver_out)}'"])

    uvfits_out = uvaver_out.with_suffix(uvaver_out.suffix + ".fits")
    logger.info(f"Creating uvfits file {uvfits_out}")
    call([f"fits", f"in='{str(uvaver_out)}'", f"out='{(uvfits_out)}'", 'op=uvout'])

    ms_out = uvaver_out.with_suffix(miriad_vis.suffix + ".ms")
    logger.info(f"Converting to MS {ms_out}")
    importuvfits(fitsfile=str(uvfits_out), vis=str(ms_out))

    logger.info(f"Finished creating {ms_out}")

    if clean_up:
        logger.info(f"Cleaning up files")
        files = [uvaver_out, uvfits_out]
        for file in files:
            file = Path(file)
            if not file.exists(): 
                logger.debug(f"File {file} does not exist, so can not be deleted. Skipping. ")
                continue 
    
            logger.debug(f"Removing {file}")
            if file.is_dir():
                shutil.rmtree(file)
            else:
                file.unlink()

    return ms_out


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Convert a miriad visibility file into a measurement set. "
    )

    parser.add_argument(
        "miriad_vis",
        type=Path,
        help="Path to the miriad visibility file to convert to a measurement set",
    )
    parser.add_argument(
        "-c",
        "--clean-up",
        action="store_true",
        help="Clean up the intermediary files created in the conversion",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=Path("."),
        type=Path,
        help="Directory to output the measurement set to",
    )
    parser.add_argument(
        "--field-out",
        action="store_true",
        help="Place the measurement set into a directory named after the field in the output directory",
    )
    parser.add_argument(
        "--field-name",
        type=str,
        default=None,
        help="Name of the field. If None, attempt to dereive it from the miriad file name. ",
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Produce more verbose messages'
    )

    return parser


def cli() -> None:
    parser = get_parser()

    args = parser.parse_args()

    logger.setLevel(logging.WARNING)
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    convert_miriad_to_ms(
        miriad_vis=args.miriad_vis,
        output_dir=args.output_dir,
        clean_up=args.clean_up,
        field_out=args.field_out,
        field_name=args.field_name,
    )


if __name__ == "__main__":
    cli()
