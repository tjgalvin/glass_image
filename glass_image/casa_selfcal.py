"""Steps and tasks for self-calibration
"""
import shutil
from pathlib import Path
from time import sleep

from casatasks import gaincal, applycal, mstransform, cvel, split

from glass_image.logging import logger
from glass_image.pointing import Pointing
from glass_image.utils import remove_files_folders
from glass_image.options import CasaSCOptions

def derive_apply_selfcal(in_point: Pointing, options: CasaSCOptions) -> Pointing:
    logger.info(f"Will apply self-calibration to {in_point.ms}")

    caltable = f"pcal{options.round}"
    logger.info(f"Will create solution table: {caltable}")

    outfield = f"{in_point.field}_{caltable}"
    outms = str(in_point.ms.parent / f"{outfield}.{'.'.join(str(in_point.ms.name).split('.')[1:])}")
    transform_ms_str = f"{outms}_transform"

    logger.info(f"Output measurement set: {outms}")

    # Creating return structure now. The output MS will be created either by:
    # - the original MS being copied in the case where the field was blank and no cleaning was performed, or
    # - self-calibration was performed
    out_point = Pointing(workdir=in_point.workdir, field=in_point.field, ms=Path(outms))

    logger.info(f"MSTransforming to {transform_ms_str} with {options.nspw} SPWs")
    mstransform(
        vis=str(in_point.ms),
        outputvis=transform_ms_str,
        regridms=True,
        nspw=options.nspw,
        mode="channel",
        nchan=-1,
        start=0,
        width=1,
        chanbin=1,
        createmms=False,
        datacolumn="all",
        combinespws=False,
    )

    logger.info(
        f"Deriving gain solutions {caltable} with solint {options.solint} and calmode {options.calmode}"
    )
    gaincal(
        vis=transform_ms_str,
        caltable=caltable,
        solint=options.solint,
        calmode=options.calmode,
        minsnr=0,
    )

    caltable_path = Path(caltable)
    if not caltable_path.exists():
        logger.warn(f"{caltable} was not created. Returning {in_point.ms}. Will copy the MS into for later rounds. ")
        
        shutil.copytree(
            in_point.ms, out_point.ms
        )
        return out_point
        
    logger.info(f"Solutions derived. Applying to data. ")

    # This will create a CORRECTED_DATA columns
    applycal(vis=transform_ms_str, gaintable=caltable)

    logger.info(f"Spliting the CORRECTED_DATA column out")
    in_ms_str = str(in_point.ms)
    split_ms_str = f"{in_ms_str}_split"

    split(vis=transform_ms_str, outputvis=split_ms_str, datacolumn="corrected")

    logger.info("Transforming to a single spectral window")

    cvel(
        vis=split_ms_str,
        outputvis=outms,
        mode="channel_b",
    )

    logger.info(f"Solutions applied. Created {out_point.ms}")

    remove_files_folders([Path(file) for file in (caltable, transform_ms_str, split_ms_str)])

    return out_point
