"""Contains glass_image errors
"""

class ImagerConfigurationError(Exception):
    """The YAML file for the imager specification is not correctly formed. 
    """
    
class FITSCleanMaskNotFound(Exception):
    """The intended FITS clean mask was not found. 
    """