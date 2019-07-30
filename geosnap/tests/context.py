import os
import sys
from warnings import warn
import quilt3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import analyze
import data


def quilt_check():

    # get census data from spatialucr quilt account
    try:  # if any of these aren't found, the user needs to refresh the quilt data package
        from quilt3.data.census import tracts_cartographic, administrative
    except AttributeError:
        warn(
            "Quilt data is outdated... rebuilding\n"
            " You will need to restart your Python kernel once downloading has completed"
        )
        quilt3.Package.install("census/tracts_cartographic", "s3://quilt-cgs")
        quilt3.Package.install("census/administrative", "s3://quilt-cgs")
