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

def derive_weight_map(mir_app_img: Path) -> None:
    """Compute a weight map through miriad machinary that corresponds 
    to the input image. The map is going to be the inverse of the primary beam
    squared

    Args:
        mir_app_img (Path): Miriad image that will have the weight map generated for
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
        ["maths", f"exp=1./<{str(mir_sens_img)}>**2.0", f"out={str(mir_weight_img)}"]
    )

    logger.info(f"Writing {str(fits_weight_img)}")
    call(
        ["fits", f"in={str(mir_weight_img)}", f"out={str(fits_weight_img)}", "op=xyout"]
    )

    remove_files_folders(
        [mir_sens_img, mir_weight_img]
    )


def apply_miriad_pb(fits_app_img: Path) -> None:
    if not fits_app_img.exists():
        raise FileNotFoundError(f"The fukes {fits_app_img} does not exist. Exiting. ")

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

    derive_weight_map(mir_app_img=mir_app_img)

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
