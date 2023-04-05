"""Functionality related to the loading and operation of the 
configuration based imaging specification
"""

from pathlib import Path
import yaml 
from typing import Any, Dict

from glass_image.logging import logger 
from glass_image.errors import ImagerConfigurationError
from glass_image.options import WSCleanOptions, CasaSCOptions, ImageRoundOptions

OPTIONTYPES = ('casasc', 'wsclean')


def load_yaml_configuration(yaml_config: Path) -> Dict[Any, Any]:
    """Load in a image configuration file that directs imaging and self-calibration

    Args:
        yaml_config (Path): Path to a YAML configuration file

    Returns:
        Dict[Any, Any]: Loaded imager parame
    """
    logger.info(f"Loading configuration file {str(yaml_config)}")
    with open(yaml_config, 'r') as in_config:
        config = yaml.load(
            in_config,
            yaml.Loader
        )
        
    return config 

def verify_configuration(yaml_config: Path):
    """Perorms basic sanity checks against an imager configuration file

    Args:
        yaml_config (Path): Path to the imager configuration file

    Raises:
        ImagerConfigurationError: Errors detected in the configuration file
    """
    config = load_yaml_configuration(yaml_config=yaml_config)

    issues = []
    for key in config['sc']:
        if not isinstance(key, int):
            issues.append(f"The key {key} of sc should be an int. ")
        if not all([k in config['sc'][key] for k in OPTIONTYPES]):
            issues.append(f"Key {key} of sc needs to have either {OPTIONTYPES}. Currently has neither. ")

    if len(issues) > 0:
        raise ImagerConfigurationError("\n".join(issues))

def get_imager_options(yaml_config: Path) -> Dict[Any, Any]:
    """Returns settings related to the general imager properties
    as a dictionary. 

    Args:
        yaml_config (Path): Path to YAML file containing the imager configuration

    Raises:
        ImagerConfigurationError: Error raised when no glass entry found. 

    Returns:
        Dict[Any, Any]: Imager related options
    """
    config = load_yaml_configuration(yaml_config)
    
    if 'glass' not in config.keys():
        raise ImagerConfigurationError(f"Imager configuration file missing 'glass' entry. ")

    return config['glass']

def get_round_options(yaml_config: Path, img_round: int) -> ImageRoundOptions:
    """Returns options specific to a single imaging / self-calibration round. If
    the is the first image round, generic self-calibration options are return. In
    the imager configuration, round 0 corresponds to the initial image _outside_
    the self-calibration->image loop. 
    
    Rounds >= 1 are where both self-calibration and wsclean options are returned
    with informative (specified) parameters. 

    Args:
        yaml_config (Path): Path to the imager configuration file
        img_round (int): Imager round. 0 implies first image with no self-calibration. 

    Raises:
        ImagerConfigurationError: Raised when configuration file not correctly formed. 

    Returns:
        ImageRoundOptions: Imaging and self-calibration options
    """
    
    config = load_yaml_configuration(yaml_config)
    
    if img_round == 0:
        return ImageRoundOptions(
            wsclean = WSCleanOptions(round=0, **config['default']['wsclean']), 
            casasc = CasaSCOptions(round=0)
        )
    
    logger.debug("Loading the defaults")
    casa_config_args = config['default']['casasc']
    wsclean_config_args = config['default']['wsclean']
    
    sc_configs = config['sc']
    if img_round in sc_configs.keys():
        logger.info(f"Image round {img_round} in configuration file")
        round_config = sc_configs[img_round]
        logger.debug(f"SC round config: {round_config}")
    
        valid = False
        for (key, args) in zip(['casasc', 'wsclean'], [casa_config_args, wsclean_config_args]):
            if key in round_config.keys():
                logger.debug(f"Found {key} in config for {img_round=}. Updating defaults. ")
                args.update(round_config[key])
                valid = True
    
        if not valid:
            raise ImagerConfigurationError(f"Neither 'casasc' now 'wsclean' options for {img_round=} found in {str(yaml_config)}")
    
    return ImageRoundOptions(
        wsclean=WSCleanOptions(round=img_round, **wsclean_config_args), 
        casasc=CasaSCOptions(round=img_round, **casa_config_args)         
    )
        
        
    
