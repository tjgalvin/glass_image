"""Utilities to convert the miriad visibility data into a measurement set
"""
import shutil
import numpy as np
import logging
from pathlib import Path
from argparse import ArgumentParser
from typing import Optional
from collections import Counter

from casatasks import importmiriad
from pyrap import tables

from glass_image.logging import logger
from glass_image.utils import remove_files_folders, ensure_dir_exists, call

def remove_nonconformant_timesteps(target_ms: Path, baselines: int=15) -> None:
    """Some ATCA measurement sets has a strange number of TIMESTEPS recorded, which
    cause an error to be raised during the self-calibration loop in the mstransform
    task. Remove there baselines. This function will remove the offending TIMESTEPS
    and produce a new measurement set. All timesteps that do not have the prescribed
    number of baselines are flaggede.  

    Args:
        target_ms (Path): The measurement set to scan and correct. 
        baselines (int, optional): The required number of baselines to be present. Defaults to 15.
    """
    logger.info(f"Searching for non-conformant time steps in {target_ms}")

    logger.info(f"Will ensure {baselines} aselines in each step")
    logger.debug(f"Opening {target_ms}")
    tab = tables.table(str(target_ms))
    
    counts = Counter(tab.getcol('TIME'))
    mask = [counts[i] == 15 for i in tab.getcol('TIME')]
    
    total_timesteps = len(mask)
    valid_timesteps = np.sum(mask)
    
    logger.info(f"{valid_timesteps} of {total_timesteps} had {baselines} baselines. ")
    
    if valid_timesteps == total_timesteps:
        logger.info("All timesteps are valid. Returning without producing corrected MS. ")
        
        return
    
    # Create a temporary output for the valid MS, so that the open
    # lock through the pyrap tables is not broken.
    nonconform_ms = target_ms.with_suffix(target_ms.suffix + '_nonconform')    
    temp_ms = target_ms.with_suffix(target_ms.suffix + '_temp')    
    
    idx = np.arange(np.array(mask).shape[0])[mask]
    sub_tab = tab.selectrows(idx) 
    
    logger.info(f"Writing out {temp_ms}")
    sub_tab.copy(str(temp_ms), deep=True)

    tab.close()

    logger.info(f"Renaming {target_ms} to {nonconform_ms}.")
    target_ms.rename(nonconform_ms)
    
    logger.info(f"Renaming {temp_ms} to {target_ms}.")
    temp_ms.rename(target_ms)

    
def extract_field_name(miriad_vis: Path) -> str:
    """Parses the name of a miriad visibilty file to extract the 
    name of the field. This assumes to (miriad standard) naming 
    convention of `field.frequency`

    Args:
        miriad_vis (Path): Path to the miriad visibility file

    Returns:
        str: Extract field name
    """
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
    force_conformant_ms: bool = False
) -> Path:
    """Converts a miriad visibility file into a measurement set. Temporary files
    created in this process can optionally be removed. Internally the CASA task
    `importmiriad` is used to handle the conversion.

    Args:
        miriad_vis (Path): Name of the miriad visivility file to convert. 
        output_dir (Path): Location to write the output measurement set to.
        clean_up (bool, optional): Remove files related to the transformation of the formats. Defaults to True.
        field_out (bool, optional): Create a folder for the field to place the measurement set into. If True and `field_name` is unset the name is extracted from the miriad visibility name. Defaults to False.
        field_name (Optional[str], optional): Provide a specific field name. Defaults to None.
        force_conformant_ms (bool, optional): Attempt to applied data cleaning operations to ensure the output measurement set is correctly formed. This is largely unnecesssary since `importmiriad` was adopted. Defaults to False.

    Returns:
        Path: Path to the output measurement set. 
    """
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

    ms_out = uvaver_out.with_suffix(miriad_vis.suffix + ".ms")
    logger.info(f"Converting to MS {ms_out}")
    importmiriad(mirfile=str(uvaver_out), vis=str(ms_out), tsys=True)

    if force_conformant_ms:
        remove_nonconformant_timesteps(ms_out)        

    logger.info(f"Finished creating {ms_out}")

    if clean_up:
        logger.info(f"Cleaning up files")
        remove_files_folders([uvaver_out])
        
    return ms_out


def get_parser() -> ArgumentParser:
    """Generates the arguement parser for the glass_vis2ms task. 

    Returns:
        ArgumentParser: Parser with populated options. 
    """
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
    """CLI entry point for the `glass_vis2ms` program. 
    """
    parser = get_parser()

    args = parser.parse_args()

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
