# Testing


## Unittesting
`geosnap` uses [pytest](https://docs.pytest.org/en/latest/index.html) for its unittesting framework.
Running the full test suite requires the [installation](https://github.com/spatialucr/geosnap/blob/master/examples/01_getting_started.ipynb) of two proprietary datasets.
The appropriate zip archives for these datasets should be placed in a single directory, and the
environment variable `$DLPATH` should be set to its path. If that variable is not present, tests
depending on these data will be skipped. 

Currently, TravisCI is configured to set the necessary environment variables for builds originating from the `spatialucr` account (i.e. *not* for PRs).
PR's will instead trigger a CI build that omits datasets but tests all other functionality

## Example Testing

In addition to unit tests, all functionality in `geosnap` should be documented in the
[example notebooks](https://github.com/spatialucr/geosnap/tree/master/examples). To ensure these
examples execute faithfully, a CI suite should ensure that the notebooks are also run using
`nbconvert`. Currently, TravisCI is set to run these notebooks only when the full test suite
completes successfully (otherwise what's the point?)