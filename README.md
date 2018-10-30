# Open Source Neighborhood Analysis Package

<img src="osnap/doc/osnap.png" alt="osnap" width="500"/>


## osnap modules

- `osnap.data`:           Ingest, create, and manipulate space-time datasets
- `osnap.analytics`:      Analyze neighborhood dynamics
- `osnap.harmonize`:      Harmonize neighborhood boundaries over time using spatial statistical methods
- `osnap.visualization`:  Visualize neighborhood dynamics

## Installation
The recommended method for installing OSNAP, is with [anaconda](https://www.anaconda.com/download/).

To get started with the development version, clone this repository or download it manually then run the following commands:

`cd osnap`
`conda env create -f environment.yml`
`python setup.py develop`
`source activate osnap`

This will download the appropriate dependencies and install OSNAP in its own conda environment 

## Development

osnap development is hosted on [github](https://github.com/spatialucr/osnap)


## Bug reports

To search for or report bugs, please see osnap's [issues](http://github.com/spatialucr/osnap/issues)


## License information

See the file "LICENSE.txt" for information on the history of this
software, terms & conditions for usage, and a DISCLAIMER OF ALL
WARRANTIES.
