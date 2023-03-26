# Version 0.1.3
## What's new

- Added a `fitsmask` option to `WSCleanOptions` to allow a clean mask in a fits format to be specified. This is expected to be produced by `glass_cleanmask`, and does not support custom mask files to be specified by name. It will look for a standard file name format produced by `glass_cleanmask`, something like `field_clean_mask.fits`, where `field` is the name portion of the measurement set. 

# Version 0.1.2
## What's new

- Added `glass_cleanmask` to extract a clean mask. A wsclean image would be temporarily created to get the expected image header out.

# Version 0.1.1
## What's new

- A configuration based approach to specifying the logic of imaging and self-calibration rounds
