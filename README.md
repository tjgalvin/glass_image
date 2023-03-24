# Example GLASS imaging script

A set of utilities to image data from the GLASS project. These codes are not concerned with data calibration, which is performed in `miriad` using a different set of scripts. 

Imaging is performed using a combination of `wsclean` for image deconvolution and `casa` for self-calibration. 

# Software Requirements

Aside from the `python` modules installed under this module, these codes require:
- `singularity`
- `miriad`

Otherwise, all `python` dependencies are specifiede in the `pyproject.toml` file, which was created and managed with `poetry`. 

# Installation

At the moment the code is not hosted on `pypi`. Installation can be performed by cloning this repository, and `pip` installing. 

It is recommended that this is done within a virtual environment where `python==3.8` has been set as the interpreter. This version of `python` is the most recent supported by `casatools`, which is the module `python` interface into `casa` that these codes are using. 

An example of creating a virtual environment using `conda`:

```
conda create -n glass_image python==3.8
conda activate glass_image
pip install git+https://github.com/tjgalvin/glass_image.git
```

# Tools

There are two scripts currently made available:

- `glass_vis2ms`: Converts a `miriad` visbility file to a measurement set
- `glass_image`: Uses `wsclean` for imaging and `casa` for self-calibration. It is driven by a yaml file that outlines imaging and self-calibration parameters used over rounds
- `glass_pbimage`: Primary beam correct an image using `miriad` and produce a corresponding wight map for use in co-adding in other programs, i.e. swarp

These tools are made available as callable programs once the `glass_image` has been installed. 

# Imager Configuration File

A very primative yaml configuration file has been defined to help describe the type of imaging and self-calibration that owuld be performed. It was initially intended to help ease the difficulty in modifying the settings directly in the code. There are examples of the configuraiton file under the `configs` directory. 

# Supported Versions

This package relies on `casatools` and `casatasks`. At time of writing the `catatools` package supports up to `python==3.8`. 