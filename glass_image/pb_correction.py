"""Components to apply a primary beam correction to 
wsclean produced images
"""
import shutil
import logging
from pathlib import Path
from argparse import ArgumentParser

from astropy.io import fits

from glass_image.utils import remove_files_folders, call
from glass_image.logging import logger
from glass_image.image_utils import img_mad

def derive_weight_map(mir_app_img: Path, rms: float = 1.0) -> Path:
    """Compute a weight map through miriad machinary that corresponds 
    to the input image. The map is going to be the inverse of the primary beam
    squared

    Args:
        mir_app_img (Path): Miriad image that will have the weight map generated for
        rms (float): The RMS of the image, which is used in the scaling of the weight map. 
    
    Returns: 
        Path -- The weight map
    """

    mir_sens_img = mir_app_img.with_suffix('.sens')
    mir_weight_img = mir_app_img.with_suffix('.weight')
    fits_weight_img = mir_weight_img.with_suffix('.weight.fits')

    logger.debug(f"Producing sensitivity map.")
    call(
        ["linmos", 
         f"in={str(mir_app_img)}", 
         f"out={str(mir_sens_img)}", 
         "rms=1", 
         "options=sensitivity"]
    )
    
    logger.debug(f"Converting to a weight map. ")
    call(
        ["maths", f"exp=1/<{str(mir_sens_img)}>**2.0", f"out={str(mir_weight_img)}"]
    )

    logger.info(f"Writing {str(fits_weight_img)}")
    call(
        ["fits", f"in={str(mir_weight_img)}", f"out={str(fits_weight_img)}", "op=xyout"]
    )

    remove_files_folders(
        [mir_sens_img, mir_weight_img]
    )

    logger.info(f"Scaling weight map by rms-squared.")
    with fits.open(str(fits_weight_img), mode='update') as open_fits_weight:
        open_fits_weight[0].data /= rms ** 2.

        open_fits_weight.flush()

    return fits_weight_img

def apply_miriad_pb(fits_app_img: Path) -> None:
    if not fits_app_img.exists():
        raise FileNotFoundError(f"The file {fits_app_img} does not exist. Exiting. ")

    logger.info(f"Estimating noise in {fits_app_img}.")
    img_std = img_mad(fits_app_img) * 1.4826 # MAS to Std. Dev. 
    logger.info(f"Estimated noise is {img_std * 1000 * 1000:.2f}uJy")

    img_header = fits.getheader(str(fits_app_img))

    nu_bw = img_header["CDELT3"]
    logger.info(f"Bandwidth of {fits_app_img} is {nu_bw} Hz")

    # Create the miriad file paths for the input/corrected miriad images
    mir_app_img = fits_app_img.with_suffix(".restor")
    mir_int_img = fits_app_img.with_suffix(".pbcorr")

    # Output fits image
    fits_int_img = fits_app_img.with_suffix(".pbcorr" + fits_app_img.suffix)

    call(["fits", f"in={str(fits_app_img)}", f"out={str(mir_app_img)}", "op=xyin"])

    logger.info("Image imported, running linmos. ")
    call(
        [
            "linmos",
            f"in={str(mir_app_img)}",
            f"out={str(mir_int_img)}",
            f"bw={int(nu_bw/1e9)},10",
        ]
    )

    logger.info(f"Created {mir_int_img}, exporting FITS image.")
    call(["fits", f"in={str(mir_int_img)}", f"out={str(fits_int_img)}", "op=xyout"])

    derive_weight_map(mir_app_img=mir_app_img, rms=img_std)

    logger.info("Removing miriad files")
    remove_files_folders([mir_app_img, mir_int_img])
    
    

def get_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Perform primary beam correction for a wsclean produced iamge"
    )

    parser.add_argument(
        "image",
        type=Path,
        help="The FITS image produced by wsclean to primary beam correct. ",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose logging mode"
    )

    return parser


def cli() -> None:
    parser = get_parser()

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    apply_miriad_pb(fits_app_img=args.image)


if __name__ == "__main__":
    cli()
