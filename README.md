# Example GLASS imaging script

A set of utilities to image data from the GLASS project. These codes are not concerned with data calibration, which is performed in `miriad` using a different set of scripts. 

Imaging is performed using a combination of `wsclean` for image deconvolution and `casa` for self-calibration. 

# Software Requirements

Aside from the `python` modules installed under this module, these codes require:
- `singularity`
- `miriad`

Otherwise, all `python` dependencies are specifiede in the `pyproject.toml` file, which was created and managed with `poetry`. 

# A note on containers

Within this code singularity is leverage to call compiled software that was not available on the HPC (or did not have the version I wanted). Specifically:

- `wsclean`: a widefield image deconvolution code. An additional CLI argument `-force-max-rounds` was added to it for SPICE-RACS processing requirements. Since these changes have not been pulled into the main repositories, this container will have to be provided (or pulled fromn `singularity pull docker://alecthomson/wsclean:force_mask`)
- `SWarp`: used for image co-adding. At the moment this is not strictly needed by the scripts in this code base. Instead the weights maps produced by `glass_obimage` are intended to be passed over to `SWarp` to linear mosaic together. A special version of `SWarp` is maintained at [my fork of `SWarp`](https://github.com/tjgalvin/swarp/tree/big). This fork applied a fix that would otherwise blank pixels whose weights were above an arbitary threshold - a threshold appropriate for optical images but not radio. An example `SWarp` template is provided as `configs/coadd.swarp`. Building this software is relatively straight forwar. 
  
# Miriad

As far as is known, `miriad` is the only other application that is required to be installed and available on the system. This repository does not make any attempt to verify or install `miriad`. It is expected to be available on the system `PATH`. 

`miriad` is used for two stages:
- in `glass_vis2ms` when converting a v`miriad` visibility file to a measurement set (it uses `uvaver` to apply any existing calibration tables to the data),
- in `glass_pbimage` when importing images (`fits`), applying a primary beam correction (`linmos`), and computing a weight map to be used with `SWarp`.

# CASA

`CASA` is used by components of this code, but it is **not** the `CASA` interative shell version that is required. It is the `casatasks` version, which exposes each of the `CASA` programs as importable python functions. These functions are used when:

- converting the `miriad` visibilities into a measurement set form
- when performing self-calibration

When developing this, `python==3.8` was the latest version supported by this `casatasks` python module. Also, there is also the `casadata` module that should be installed (automatically by this `pyproject.toml` specification used by `pip`) that should download all the appropriate MEASURES tables. Note though that this last stage is, in my experience, not always reliable and can be a source of frustration. There is not a silver bullet here, and might require manual intervention if strange errors are thrown by `CASA` related tasks. 

# Installation

At the moment the code is not hosted on `pypi`. Installation can be performed by cloning this repository, and `pip` installing. 

It is recommended that this is done within a virtual environment where `python==3.8` has been set as the interpreter. This version of `python` is the most recent supported by `casatools`, which is the module `python` interface into `casa` that these codes are using. 

An example of creating a virtual environment using `conda`:

```
conda create -n glass_image python==3.8
conda activate glass_image
pip install git+https://github.com/tjgalvin/glass_image.git
```

Note that this approach requires a working `conda` installation. If that is not available, try to make it so. Alternatively, so long as there is a `python3.8` available on the host HPC system, a `venv` could be created. 

# Tools

There are two scripts currently made available:

- `glass_vis2ms`: Converts a `miriad` visbility file to a measurement set
- `glass_image`: Uses `wsclean` for imaging and `casa` for self-calibration. It is driven by a yaml file that outlines imaging and self-calibration parameters used over rounds
- `glass_pbimage`: Primary beam correct an image using `miriad` and produce a corresponding wight map for use in co-adding in other programs, i.e. swarp
- `glass_cleanmask`: Create a clean mask for a pointing, extracted from a large clean mask image. The intention is that a region will be co-added to give optimal sensitivity, then a 'signal' image will be created. The creation of this signal map and the corresponding thresholding is not currently performed by this code. 

These tools are made available as callable programs once the `glass_image` has been installed. 

The order that the tasks appear above corresponds to the order in which they should be called. Each task operates on a single pointing. If there are many pointings that need to be processed, then each task needs to be called once per pointing. 

## Convolving to a common resolution

The keen eyed may notice that there are no tasks / code in this repository that convolves images to a common resolution. To that end, uses the `beamcon_2D` program from `racs_tools`, which can be `pip` installed:

```
pip install RACS-tools
```

Given an appropriate compute or interactive node, something as simple as 

```
beamcon_2D -o convolved_images --conv_mode robust --ncores 6 /glob/expression/to/images/here
```

The output of this task should be the set of images that are co-added together.

There is an example SLURM submittable script that could be used as well. 

# SLURM Scripts

A collection of SLURM scripts are provided that could be used to operate on each pointing for `glass_image` tasks that are long running and require a lot fo compute. They can be used and modified as needed. Generally they accept a single input that points to the field to process, e.g. 

```
sbatch run_glass_image.sh /path/to/a/field/a_1233.ms
```

There is no SLURM submittable script for the `glass_vis2ms`. This task is fairly inexpensive to run, so could be done on an interactive node fairly safely. 

# Imager Configuration File

A very primative yaml configuration file has been defined to help describe the type of imaging and self-calibration that owuld be performed. It was initially intended to help ease the difficulty in modifying the settings directly in the code. There are examples of the configuration file under the `configs` directory. 

```
glass:
  rounds: 4
default:
  casasc:
   solint: "40s"
   nspw: 4
   calmode: "p"
  wsclean:
   psfwindow: 65
   size: 7000
   forcemask: 10
   maskthresh: 5
   autothresh: 0.5
   channels_out: 8

sc: 
  1:
    casasc:
      nspw: 4
      solint: "10s"
    wsclean:
      psfwindow: 50
      maskthresh: 6.0
        
  2:
    casasc:
      nspw: 4
      solint: "10s"
    wsclean:
      psfwindow: 50
      maskthresh: 6.0
        
  3:
    casasc:
      nspw: 4
      solint: "10s"
```

Above is an example of a imager configuration YAML file that could be given to `glass_image`. The fields under `casasc` and `wsclean` would be provided as overriding values to the defaults in the code. These options are all under `glass_image/options.py`. If a value is not listed in this YAML file (either under the `defaults` entry or a `sc` specific entry) then the values passed to `CASA`s `gaincal` and `wsclean` are taken from these static values. Fields under the `defaults` YAML field are used to replace the statically defined variables (i.e. they become global values unless explcitily overwritten).

The `sc` field denotes the options to be used for each round of self-calibration. 

The `glass.rounds` field denotes how many rounds of self-calibration to perform. This can be increased or decreased as necessary.

## A reminder

When this code was slapped togethert in April 2023, it was the wild wild west. Upon inspection by Minh Huyn it was found that these self-calibration settings were far from optimal. The short time solutions could cause faint sources not captured by the clean model to be 'phased-out'. It is suggested that these numbers be increased from the example `10s` to something larger, say `5min`. 


# Supported Versions

This package relies on `casatools` and `casatasks`. At time of writing the `catatools` package supports up to `python==3.8`. 
