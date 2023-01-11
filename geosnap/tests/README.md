# Testing

## Unittesting

`geosnap` uses [pytest](https://docs.pytest.org/en/latest/index.html) for its unittesting framework.
Running the full test suite requires the
[installation](https://github.com/oturns/geosnap/blob/main/examples/01_getting_started.ipynb)
of two proprietary datasets. It also requires four environment variables to be set:

- `$NCDB`, `$LTDB_SAMPLE`, `$LTDB_FULLCOUNT` : these just need to be set. Any value will do. If these are not set, any tests dependent on LTDB or NCDB data will be skipped.
- `$GITHUB_WORKSPACE` : path to the local directory containing these files (i.e. after collecting from their remote locations in a prior CI phase). If this is not set, the test will assume files are located in the current directory

The data must be installed prior to running the test suite, otherwise the kernel needs to be
restarted. The easiest way to accomplish this is to run the `get_data.py` script as the final step
of the installation phase in a CI build. The script fails silently if the environment variables
aren't set or the data are not present, so it can be executed on every build.

Currently, GHActions is configured to set the necessary environment variables for builds originating
from the `spatialucr` account (i.e. *not* for PRs). PR's will instead trigger a CI build that omits
datasets but tests all other functionality.

## Example Testing

In addition to unit tests, all functionality in `geosnap` should be documented in the
[example notebooks](https://github.com/oturns/geosnap/tree/main/examples). To ensure these
examples execute faithfully, a CI suite should ensure that the notebooks are also run using
`nbconvert`. Currently, TravisCI is set to run these notebooks only when the full test suite
completes successfully (otherwise what's the point?)
