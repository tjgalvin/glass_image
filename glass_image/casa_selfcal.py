"""Steps and tasks for self-calibration
"""
from pathlib import Path

from casatasks import gaincal, applycal, mstransform

from glass_image.logging import logger
from glass_image.pointing import Pointing

def derive_apply_selfcal(in_point: Pointing, img_round: int=0) -> Pointing:
    logger.info(f"Will apply self-calibration to {in_point.ms}")

    caltable = f"pcal{img_round}"
    logger.info(f"Will create solution table: {caltable}")
    
    gaincal(
        vis=str(in_point.ms),
        caltable=caltable,
        solint='60s',
        calmode='p'
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
        nspw=2,
        outputvis=outms
    )
    
    out_point = Pointing(
        workdir=in_point.workdir,
        field=outfield,
        ms=Path(outms)
    )
    
    logger.info(f"Created {out_point}")
    
    return out_point
    
    