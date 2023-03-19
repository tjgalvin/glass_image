"""Steps and tasks for self-calibration
"""
import shutil
from pathlib import Path
from typing import NamedTuple

from casatasks import gaincal, applycal, mstransform, cvel, split

from glass_image.logging import logger
from glass_image.pointing import Pointing

class CasaSCOptions(NamedTuple):
    solint: str = '60s'
    nspw: int = 4
    calmode: str = 'p'

def selfcal_round_options(img_round: int) -> CasaSCOptions:
    logger.debug(f"Getting options for self-calibration")
    
    options = CasaSCOptions(nspw=1)
    
    if img_round == 1:
        options = CasaSCOptions(
            solint='60s',
            nspw=4
        )
    if img_round in (2, 3):
        options = CasaSCOptions(
            solint='10s',
            nspw=4
        )
    if img_round >= 4:
        options = CasaSCOptions(
            solint='10s',
            nspw=6
        )

    logger.info(f"Self-calibration options: {options}")
    
    return options

def derive_apply_selfcal(in_point: Pointing, img_round: int=0) -> Pointing:
    logger.info(f"Will apply self-calibration to {in_point.ms}")

    caltable = f"pcal{img_round}"
    logger.info(f"Will create solution table: {caltable}")

    options = selfcal_round_options(img_round=img_round)
    
    gaincal(
        vis=str(in_point.ms),
        caltable=caltable,
        solint=options.solint,
        calmode=options.calmode
    )
    
    logger.info(f"Solutions derived. Applying to data. ")
    
    # This will create a CORRECTED_DATA columns
    applycal(
        vis=str(in_point.ms),
        gaintable=caltable
    )

    outfield = f"{in_point.field}_{caltable}"
    outms = f"{outfield}.{'.'.join(str(in_point.ms.name).split('.')[1:])}"

    logger.info(f"Attempting to concatenate SPWs together")
    in_ms_str = str(in_point.ms)
    concat_ms_str = f"{in_ms_str}_concat"
    
    cvel(
        vis=in_ms_str,
        outputvis=concat_ms_str,
        mode='channel_b',
    )

    logger.info("Solutions applied. Regridding the MS and removing old DATA column. ")
    mstransform(
        vis=concat_ms_str,
        outputvis=outms,
        regridms=True,
        nspw=options.nspw,
        mode='channel',
        nchan=-1,
        start=0,
        width=1,
        chanbin=1,
        createmms=False,
        datacolumn='corrected',
        combinespws=False
    )
    
    out_point = Pointing(
        workdir=in_point.workdir,
        field=in_point.field,
        ms=Path(outms)
    )
    
    logger.info(f"Created {out_point.ms}")
    
    ms_concat_path = Path(concat_ms_str)
    logger.info(f"Removing {ms_concat_path}")
    shutil.rmtree(ms_concat_path)
    
    return out_point
    
def derive_apply_selfcal2(in_point: Pointing, img_round: int=0) -> Pointing:
    logger.info(f"Will apply self-calibration to {in_point.ms}")

    options = selfcal_round_options(img_round=img_round)

    caltable = f"pcal{img_round}"
    logger.info(f"Will create solution table: {caltable}")

    outfield = f"{in_point.field}_{caltable}"
    outms = f"{outfield}.{'.'.join(str(in_point.ms.name).split('.')[1:])}"
    transform_ms_str = f"{outms}_transform"

    logger.info(f"MSTransforming to {transform_ms_str} with {options.nspw} SPWs")
    mstransform(
        vis=str(in_point.ms),
        outputvis=transform_ms_str,
        regridms=True,
        nspw=options.nspw,
        mode='channel',
        nchan=-1,
        start=0,
        width=1,
        chanbin=1,
        createmms=False,
        datacolumn='all',
        combinespws=False
    )

    logger.info(f"Deriving gain solutions {caltable} with solint {options.solint} and calmode {options.calmode}")
    gaincal(
        vis=transform_ms_str,
        caltable=caltable,
        solint=options.solint,
        calmode=options.calmode
    )
    
    logger.info(f"Solutions derived. Applying to data. ")
    
    # This will create a CORRECTED_DATA columns
    applycal(
        vis=transform_ms_str,
        gaintable=caltable
    )

    logger.info(f"Spliting the CORRECTED_DATA column out")
    in_ms_str = str(in_point.ms)
    split_ms_str = f"{in_ms_str}_split"
    
    split(
        vis=transform_ms_str,
        outputvis=split_ms_str,
        datacolumn='corrected'
    )
    
    cvel(
        vis=split_ms_str,
        outputvis=outms,
        mode='channel_b',
    )

    out_point = Pointing(
        workdir=in_point.workdir,
        field=in_point.field,
        ms=Path(outms)
    )
    
    logger.info(f"Solutions applied. Created {out_point.ms}")
    
    for remove_ms in (transform_ms_str, split_ms_str):
        logger.info(f"Removing {remove_ms}")
        shutil.rmtree(remove_ms)
    
    return out_point
    
    
    
    