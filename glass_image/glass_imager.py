"""The main script runner for GLASS imager
"""
import os
from argparse import ArgumentParser
from pathlib import Path

from glass_image.wsclean import pull_wsclean_container, generate_wsclean_cmd, run_wsclean_cmd
from glass_image.logging import logger 
from glass_image.pointing import GPointing


def image_round(wsclean_img: Path, point: GPointing):
    
    logger.info(f"Will be imaging {point}")
    logger.info(f"Using container: {wsclean_img=}")
    
    cmd = generate_wsclean_cmd(point=point, round=0)
    
    run_wsclean_cmd(wsclean_img=wsclean_img, wsclean_cmd=cmd)
    
    
def image_cband(ms_path: Path, workdir: Path=None) -> None:
    
    assert ms_path.exists(), f"MS {ms_path} does not exist"
    
    if workdir is not None:
        logger.info(f"Changing directory to: {workdir}")
        os.chdir(workdir)
    else:
        workdir = Path(os.getcwd())
    
    logger.debug(f"Input MS: {ms_path}")
    name_comps = ms_path.name.split()
    field = "_".join(name_comps[:1])
    
    point = GPointing(
        workdir=workdir,
        field=field,
        ms=ms_path
    )
    
    wsclean_img = pull_wsclean_container()
    
    logger.info(f"Formed point: {point}")
    logger.info(f"WSClean image: {wsclean_img}")
    
      
def get_parser() -> ArgumentParser:
    parser = ArgumentParser(description="A simple imaging script for GLASS data")

    parser.add_argument('ms', type=Path, help="Path to the field to image")
    parser.add_argument('-w','--workdir', type=Path, default=None, help='Where to carry out the processing')

    return parser 

def cli() -> None:
    parser = get_parser()    
    
    args = parser.parse_args()

    image_cband(
        ms_path=args.ms,
        workdir=args.workdir
    )


if __name__ == '__main__':
    cli()
    
    