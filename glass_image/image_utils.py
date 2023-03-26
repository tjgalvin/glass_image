"""Helper functions related to interation with image data,
primarily in the FITS image format. 
"""
from pathlib import Path

import numpy as np
from astropy.wcs import WCS
from astropy.io import fits
from reproject import reproject_interp

from glass_image.logging import logger
from glass_image.pointing import Pointing
from glass_image.errors import FITSCleanMaskNotFound
from glass_image.options import ImageRoundOptions

def find_fits_mask(point: Pointing) -> Path:
    """Searches and returns the Path to the clean mask. The initial signal-cut
    mask is intended to be produced from the larger mosaic co-add of all data. 
    This FITS clean mask is to be an extract of the larger mosaic, where the region
    corresponds to the region being imaged. 

    Args:
        point (Pointing): Measurement set pointing details that the FITS clean mask corresponds to

    Returns:
        Path: Path to the generated clean ask
    """
    out_path = Path(f"{point.field}_clean_mask.fits")

    if not out_path.exists():
        raise FITSCleanMaskNotFound(out_path)
    
    return out_path


def cutout_mask(image_header: fits.header.Header, mosaic_mask: Path, point: Pointing, options: ImageRoundOptions) -> Path:
    logger.info(f"Will be extracting clean mask from {mosaic_mask}")
    
    img_npix = options.wsclean.size
    img_shape = (img_npix, img_npix)
    
    logger.debug(f"Output shape is {img_shape}")
    
    with fits.open(str(mosaic_mask)) as mask_fits:
        extract_img = reproject_interp(
                (np.squeeze(mask_fits[0].data), WCS(mask_fits[0].header).celestial),
                WCS(image_header).celestial,
                shape_out=img_shape
        )
    
    logger.info(f"Extracted image header {extract_img}")
    
    out_path = Path(f"{point.field}_clean_mask.fits")
    fits.writeto(
        str(out_path),
        extract_img[0],
        image_header,
        overwrite=True
    )

    return out_path
    
    
def img_mad(fits_img: Path) -> float:
    """Compute the Median Absolute Deviation of an image. This does not 
    perform any type of sigma clipping, and will compute the MAD over the
    whole image. This is a cheap way of avoiding an process like BANE to
    compute the background and RMS across the whole field. 

    Args:
        fits_img (Path): Path to the FITS image to compute the MAD for. 

    Returns:
        float: The MAD statisitc in the same units as the pixel data
    """
    assert fits_img.suffix == '.fits', f"{fits_img} may not be a fits image. "

    data = fits.getdata(str(fits_img))
    
    data_median = np.median(data)
    data_diff = np.abs(data - data_median)
    
    return np.median(data_diff)
