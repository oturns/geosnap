# Open Source Neighborhood Analysis Package
[![Build Status](https://travis-ci.com/spatialucr/osnap.svg?branch=master)](https://travis-ci.com/spatialucr/osnap)  [![Coverage Status](https://coveralls.io/repos/github/spatialucr/osnap/badge.svg?branch=master)](https://coveralls.io/github/spatialucr/osnap?branch=master)

<img src="osnap/doc/osnap.png" alt="osnap" width="500"/>


## osnap modules

- `osnap.data`:  
Ingest, create, and manipulate space-time datasets

- `osnap.analytics`:  
Analyze neighborhood dynamics

- `osnap.harmonize`:  
Harmonize neighborhood boundaries with spatial statistical methods

- `osnap.visualization`:    
Visualize neighborhood dynamics

## Installation
The recommended method for installing OSNAP is with [anaconda](https://www.anaconda.com/download/). To get started with the development version, clone this repository or download it manually then `cd` into the directory and run the following commands:

```bash
$ conda env create -f environment.yml
$ source activate osnap 
$ python setup.py develop
```

This will download the appropriate dependencies and install OSNAP in its own conda environment.

To get started analyzing the space-time dynamics of neighborhoods, you should install data from the Longitudinal Tract Database following these [instructions](https://github.com/spatialucr/osnap/tree/master/osnap/data/README.md).

Once the LTDB data is installed, check out the [example](https://github.com/spatialucr/osnap/tree/master/osnap/examples) directory, then start `ipython` or a Jupyter Notebook and hack away!

## Development

osnap development is hosted on [github](https://github.com/spatialucr/osnap)


## Bug reports

To search for or report bugs, please see osnap's [issues](http://github.com/spatialucr/osnap/issues)


## License information

See the file "LICENSE.txt" for information on the history of this
software, terms & conditions for usage, and a DISCLAIMER OF ALL
WARRANTIES.

## Funding
![nsf-logo](osnap/doc/nsf_logo.jpg) This project is supported by NSF Award #1733705, [Neighborhoods in Space-Time Contexts](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1733705&HistoricalAwards=false)
