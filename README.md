<p align="center">
<img height=200 src="https://github.com/oturns/geosnap/raw/main/docs/figs/geosnap_long.png" alt="geosnap"/>
</p>

<h2 align="center" style="margin-top:-10px">The Geospatial Neighborhood Analysis Package</h2> 

[![Continuous Integration](https://github.com/oturns/geosnap/actions/workflows/unittests.yml/badge.svg)](https://github.com/oturns/geosnap/actions/workflows/unittests.yml)
[![codecov](https://codecov.io/gh/oturns/geosnap/branch/main/graph/badge.svg)](https://codecov.io/gh/oturns/geosnap)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/geosnap)
![PyPI](https://img.shields.io/pypi/v/geosnap)
![Conda (channel only)](https://img.shields.io/conda/vn/conda-forge/geosnap)
![Conda](https://img.shields.io/conda/dn/conda-forge/geosnap)
![GitHub commits since latest release (branch)](https://img.shields.io/github/commits-since/oturns/geosnap/latest)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3526163.svg)](https://doi.org/10.5281/zenodo.3526163)

`geosnap` provides a suite of tools for exploring, modeling, and visualizing the social context and spatial extent of neighborhoods and regions over time. It brings together state-of-the-art techniques from [geodemographics](https://en.wikipedia.org/wiki/Geodemography), [regionalization](https://www.sciencedirect.com/topics/earth-and-planetary-sciences/regionalism), [spatial data science](https://geographicdata.science/book), and [segregation analysis](https://github.com/pysal/segregation) to support social science research, public policy analysis, and urban planning. It provides a simple interface tailored to formal analysis of spatiotemporal urban data.

<p align="center">
<img width='50%' src='https://github.com/oturns/geosnap/raw/main/docs/figs/Washington-Arlington-Alexandria_DC-VA-MD-WV.gif' alt='DC Transitions' style=' display: block; margin-left: auto; margin-right: auto; max-height: 540px'/>
</p>


## Main Features

* fast, efficient tooling for standardizing data from multiple time periods into a shared geographic representation appropriate for spatiotemporal analysis

* analytical methods for understanding sociospatial structure in neighborhoods, cities, and regions, using unsupervised ML from scikit-learn and spatial optimization from [PySAL](https://pysal.org)
  * classic and spatial analytic methods for diagnosing model fit, and locating (spatial) statistical outliers

* novel techniques for understanding the evolution of neighborhoods over time, including identifying hotspots of local neighborhood change, as well as modeling and simulating neighborhood conditions into the future

* quick access to [a large database](https://open.quiltdata.com/b/spatial-ucr) of commonly-used neighborhood indicators from U.S. providers including Census, EPA, LEHD, NCES, and NLCD, streamed from the cloud thanks to [quilt](https://quiltdata.com/) and the highly-performant [geoparquet](https://carto.com/blog/introducing-geoparquet-geospatial-compatibility/) file format.

## Why

Understanding neighborhood context is critical for social science research, public policy analysis, and urban planning. The social meaning, formal definition, and formal operationalization of ["neighborhood"](https://www.cnu.org/publicsquare/2019/01/29/once-and-future-neighborhood) depends on the study or application, however, so neighborhood analysis and modeling requires both flexibility and adherence to a formal pipeline. Maintaining that balance is challenging for a variety of reasons:

* many different physical and social data can characterize a neighborhood (e.g. its proximity to the urban core, its share of residents with a high school education, or the median price of its apartments) so there are countless ways to model neighborhoods by choosing different subsets of attributes to define them

* conceptually, neighborhoods evolve through both space and time, meaning their socially-construed boundaries can shift over time, as can their demographic makeup.

* geographic tabulation units change boundaries over time, meaning the raw data are aggregated to different areal units at different points in time.

* the relevant dimensions of neighborhood change are fluid, as are the thresholds that define meaningful change

To address those challenges, geosnap incorporates tools from the PySAL ecosystem and scikit-learn along with internal data-wrangling that helps keep inputs and outputs simple for users. It operates on long-form geodataframes and includes logic for common transformations, like harmonizing geographic boundaries over time, and standardizing variables within their time-period prior to conducting pooled geodemographic clustering.

This means that while geosnap has native support for commonly-used datasets like the Longitudinal Tract Database [(LTDB)](https://www.brown.edu/academics/spatial-structures-in-social-sciences/ltdb-following-neighborhoods-over-time), or the Neighborhood Change Database [(NCDB)](https://geolytics.com/products/normalized-data/neighborhood-change-database), it can also incorporate a wide variety of datasets, at _any_ spatial resolution, as long as the user understands the implications of the interpolation process.

## Research Questions

The package supports social scientists examining questions such as:

- Where are the socially-homogenous districts in the city?
  - Have the composition of these districts or their location shifted over time?
- What are the characteristics of prototypical neighborhoods in city or region X?
- Have the locations of different neighborhood prototypes changed over time? e.g:
  - do central-city neighborhoods show signs of gentrification?(and/or does poverty appear to be suburbanizing?)
  - is there equitable access to fair housing in high-opportunity neighborhoods (or a dearth of resources in highly-segregated neighborhoods)?
- Which neighborhoods have experienced dramatic change in several important variables? (and are they clustered together in space?)
- If spatial and temporal trends hold, how might we expect neighborhoods to look in the future?
  - how does the region look differently if units 1,2, and 3 are changed to a different type in the current time period?
- Has the region become more or less segregated over time?
  - at which spatial scales?
  - is the change statistically significant?


## Installation

We recommend installing `geosnap` via a package manager that supports installing conda packages from [conda-forge](https://conda-forge.org/). Installing directly from the Python Package Index (PyPI) is also supported.

### Installation via [Miniforge](https://github.com/conda-forge/miniforge)

```bash
mamba install -c conda-forge geosnap
```

### Installation via [Pixi](https://pixi.sh/latest/)

 Installation via `pixi` is supported, excluding `pixi global install`:

```bash
pixi init name_of_my_project
cd name_of_my_project
pixi add geosnap
```

### Installation via pip

```bash
pip install geosnap
```

### Installation via [uv](https://docs.astral.sh/uv/)

```bash
uv pip install geosnap
```

## User Guide

See the [User Guide](https://oturns.github.io/geosnap-guide/) for a
gentle introduction to using `geosnap` for neighborhood research

## API Documentation

See the [API docs](https://oturns.github.io/geosnap/api.html) for a thorough explanation of `geosnap`'s core functionality

## Development

geosnap development is hosted on [github](https://github.com/oturns/geosnap)

To get started with the development version,
clone this repository or download it manually then `cd` into the directory and run the
following commands:

```bash
conda env create -f environment.yml
conda activate geosnap 
pip install -e . --no-deps
```

This will download the appropriate dependencies and install geosnap in its own conda environment.

## Bug reports

To search for or report bugs, please see geosnap’s
[issues](http://github.com/oturns/geosnap/issues)

## License information

See the file “LICENSE.txt” for information on the history of this software, terms &
conditions for usage, and a DISCLAIMER OF ALL WARRANTIES.

## Citation

For a generic citation of geosnap, we recommend the following:

```latex
@misc{Knaap2019,
author = {Knaap, Elijah and Kang, Wei and Rey, Sergio and Wolf, Levi John and Cortes, Renan Xavier and Han, Su},
doi = {10.5281/ZENODO.3526163},
title = {{geosnap: The Geospatial Neighborhood Analysis Package}},
url = {https://zenodo.org/record/3526163},
year = {2019}
}
```

If you need to cite a specific release of the package, please find the appropriate version on [Zenodo](https://zenodo.org/record/3526163)

## Funding

<img src="docs/figs/nsf_logo.jpg" width=100 /> This project is supported by NSF Award #1733705,
[Neighborhoods in Space-Time Contexts](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1733705\&HistoricalAwards=false)
