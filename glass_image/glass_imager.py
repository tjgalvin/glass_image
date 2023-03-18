"""The main script runner for GLASS imager
"""
import os
import logging
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional

from glass_image import WSCLEANDOCKER
from glass_image.wsclean import pull_wsclean_container, generate_wsclean_cmd, run_wsclean_cmd
from glass_image.logging import logger 
from glass_image.pointing import Pointing
from glass_image.casa_selfcal import derive_apply_selfcal

def image_round(wsclean_img: Path, point: Pointing, img_round: int=0) -> None:
    
    logger.info(f"Will be imaging {point}")
    logger.info(f"Using container: {wsclean_img=}")
    
    wsclean_cmd = generate_wsclean_cmd(point=point, img_round=img_round)
    
    output_dir = Path(f"round_{img_round}") if img_round > 0 else Path("no_selfcal")
    assert not output_dir.exists(), f"Output folder {output_dir} already exists. "
    
    run_wsclean_cmd(
        wsclean_img=wsclean_img, 
        wsclean_cmd=wsclean_cmd, 
        move_into=output_dir
    )
    
     
def image_cband(ms_path: Path, workdir: Optional[Path]=None, wsclean_img: Optional[Path]=None) -> None:
    
    assert ms_path.exists(), f"MS {ms_path} does not exist"
    
    if workdir is not None:
        logger.info(f"Changing directory to: {workdir}")
        os.chdir(workdir)
    else:
        workdir = Path(os.getcwd())
    
    logger.debug(f"Input MS: {ms_path}")
    name_comps = ms_path.name.split('.')
    logger.debug(f"{name_comps}")
    field = "_".join(name_comps[:1])
    
    point = Pointing(
        workdir=workdir,
        field=field,
        ms=ms_path
    )
    
    if wsclean_img is None:
        logger.info("No wsclean-image provided. Will attempt to download. ")
        wsclean_img = pull_wsclean_container()
    
    logger.info(f"Formed point: {point}")
    logger.info(f"WSClean image: {wsclean_img}")
    
    image_round(wsclean_img=wsclean_img, point=point)
    
    for img_round in range(1, 5):
        logger.info(f"Attempting selcalibration for round {img_round}")
        selfcal_point = derive_apply_selfcal(in_point=point, img_round=img_round)
        
        logger.info(f"Running imaging for round {img_round}")
        image_round(wsclean_img=wsclean_img, point=selfcal_point, img_round=img_round)
        
      
def get_parser() -> ArgumentParser:
    parser = ArgumentParser(description="A simple imaging script for GLASS data")

    parser.add_argument('ms', type=Path, help="Path to the field to image")
    parser.add_argument('-w','--workdir', type=Path, default=None, help='Where to carry out the processing')
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose logging")
    parser.add_argument('--wsclean-image', type=Path, default=None, help=F"Path to the wsclean singularity container. If not provided will attempt to download {WSCLEANDOCKER}, a slightly modified wsclean image. ")

    return parser 

def cli() -> None:
    parser = get_parser()    
    
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    image_cband(
        ms_path=args.ms,
        workdir=args.workdir,
        wsclean_img=args.wsclean_image
    )


if __name__ == '__main__':
    cli()
    
    