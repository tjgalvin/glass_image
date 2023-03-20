"""Components to apply a primary beam correction to 
wsclean produced images
"""
from pathlib import Path

from astropy.io import fits

from glass_image.pointing import Pointing
from glass_image.utils import call
from glass_image.logging import logger

def get_img_name(in_point: Pointing) -> Path:
    logger.info("STUB FUNCTION TO RETURN FILE")
    return Path('.')

def apply_miriad_pb(in_point: Pointing) -> None:
    fits_app_img = get_img_name(in_point)
    img_header = fits.getheader(str(fits_app_img))
    
    nu_bw = img_header['CDELT3']
    logger.info(f"Bandwidth of {fits_app_img} is {nu_bw} Hz")
    
    # Create the miriad file paths for the input/corrected miriad images
    mir_app_img = fits_app_img.with_suffix('.restor')
    mir_int_img = fits_app_img.with_suffix('.pbcorr')
    
    # Output fits image
    fits_int_img = fits_app_img.with_suffix(".pbcorr"+img_path.suffix)
    
    call(
        ["fits", f"in={str(fits_app_img)}", f"out={str(mir_app_img)}", "op=xyin"]
    )
    
    logger.info("Image imported, running linmos. ")
    call(
        ["linmos", f"in={str(mir_app_img)}", f"out={str(mir_int_img)}", f"bw={int(nu_bw/1e9)}"]
    )
    
    logger.info(f"Created {mir_int_img}, exporting FITS image.")
    call(
        ["fits", f"in={str(mir_int_img)}", f"out={str(fits_int_img)}", "op=xyin"]
    )
    
    