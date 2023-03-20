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

- `glass_vis2ms`
- `glass_image`

Both are made available as callable programs once the `glass_image` has been installed. 

# Supported Versions

This package relies on `casatools` and `casatasks`. At time of writing the `catatools` package supports up to `python3.8`. 