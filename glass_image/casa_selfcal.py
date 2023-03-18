"""Steps and tasks for self-calibration
"""
from pathlib import Path
from typing import NamedTuple

from casatasks import gaincal, applycal, mstransform

from glass_image.logging import logger
from glass_image.pointing import Pointing

class CasaSCOptions(NamedTuple):
    solint: str = '60s'
    nspw: int = 1
    calmode: str = 'p'

def selfcal_round_options(img_round: int) -> CasaSCOptions:
    logger.debug(f"Getting options for self-calibration")
    
    options = CasaSCOptions(nspw=4)
    
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

    logger.info("Solutions applied. Regridding the MS and removing old DATA column. ")
    mstransform(
        vis=str(in_point.ms),
        regridms=True,
        nspw=options.nspw,
        outputvis=outms,
        datacolumn='corrected'
    )
    
    out_point = Pointing(
        workdir=in_point.workdir,
        field=outfield,
        ms=Path(outms)
    )
    
    logger.info(f"Created {out_point.ms}")
    
    return out_point
    
    