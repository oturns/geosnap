"""Utility functions for downloading Census data."""

import pandas
import sys
import geopandas as gpd
from tqdm.auto import tqdm

from pathlib import Path


def fetch_acs(
    state="all",
    level="tract",
    year=2017,
    output_dir=None,
    skip_existing=True,
    return_geometry=True,
    process_vars=True
):
    """Collect the variables defined in `geosnap.datasets.codebook` from the Census API.

    Parameters
    ----------
    level : str
        Census geographic tabulation unit e.g. "block", "tract", or "county"
        (the default is 'tract').
    state : str
        State for which data should be collected, e.g. "Maryland".
        if 'all' (default) the function will loop through each state and return
        a combined dataframe.
    year : int
        ACS release year to query (the default is 2017).
    output_dir : str
        Directory that intermediate parquet files will be written to. This is useful
        if the data request is large and the connection to the Census API fails while
        building the entire query.
    skip_existing : bool
        If caching files to disk, whether to overwrite existing files or skip them
    return_geometry : bool
        whether to return geometry data from the Census API

    Returns
    -------
    pandas.DataFrame or geopandas.GeoDataFrame
        Dataframe or GeoDataFrame containing variables from the geosnap codebook

    Examples
    -------
    >>> dc = fetch_acs('District of Columbia', year=2015)

    """
    from cenpy import products
    from .._data import datasets

    states = datasets.states()
    _variables = datasets.codebook().copy()
    acsvars = _process_columns(_variables["acs"].dropna())

    if state == "all":
        dfs = []
        with tqdm(total=len(states), file=sys.stdout) as pbar:
            for state in states.sort_values(by="name").name.tolist():
                fname = state.replace(" ", "_")
                pth = Path(output_dir, f"{fname}.parquet")

                if skip_existing and pth.exists():
                    print(f"skipping {fname}")
                    pass

                else:
                    try:
                        df = products.ACS(year).from_state(
                            state=state,
                            level=level,
                            variables=acsvars.copy(),
                            return_geometry=return_geometry,
                        )
                        if process_vars:
                            processed = process_acs(df)
                            if return_geometry:
                                processed['geometry'] = df.geometry
                                df = gpd.GeoDataFrame(processed)
                        dfs.append(df)
                        if output_dir:
                            df.to_parquet(pth)
                    except:
                        tqdm.write("{state} failed".format(state=state))

                pbar.update(1)
        df = pandas.concat(dfs)
    else:
        df = products.ACS(year).from_state(
            state=state,
            level=level,
            variables=acsvars.copy(),
            return_geometry=return_geometry,
        )

        fname = state.replace(" ", "_")
        pth = Path(output_dir, f"{fname}.parquet")

        if process_vars:
            processed = process_acs(df)
            if return_geometry:
                processed['geometry'] = df.geometry
                df = gpd.GeoDataFrame(processed)
            df.to_parquet(pth)

    return df


def process_acs(df):
    """Calculate variables from the geosnap codebook

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame contining raw census data (as processed by `fetch_acs`)
    """
    from .._data import datasets

    _variables = datasets.codebook().copy()
    evalcols = [
            _normalize_relation(rel) for rel in _variables["acs"].dropna().tolist()
        ]
    varnames = _variables.dropna(subset=["acs"])["variable"]
    evals = [parts[0] + "=" + parts[1] for parts in zip(varnames, evalcols)]

    df.set_index("GEOID", inplace=True)
    df = df.apply(lambda x: pandas.to_numeric(x, errors="coerce"), axis=1)
    # compute additional variables from lookup table
    for row in evals:
        try:
            df.eval(row, inplace=True, engine="python")
        except Exception as e:
            print(row + " " + str(e))
    for row in _variables["formula"].dropna().tolist():
        try:
            df.eval(row, inplace=True, engine="python")
        except Exception as e:
            print(str(row) + " " + str(e))
    keeps = [col for col in df.columns if col in _variables.variable.tolist()]
    df = df[keeps]
    return df


def _process_columns(input_columns):
    # prepare by taking all sum-of-columns as lists
    outcols_processing = [s.replace("+", ",") for s in input_columns]
    outcols = []
    while outcols_processing:  # stack
        col = outcols_processing.pop()
        col = col.replace("-", ",").replace("(", "").replace(")", "")
        col = [c.strip() for c in col.split(",")]  # get each part
        if len(col) > 1:  # if there are many parts
            col, *rest = col  # put the rest back
            for r in rest:
                outcols_processing.insert(0, r)
        else:
            col = col[0]
        if ":" in col:  # if a part is a range
            start, stop = col.split(":")  # split the range
            stem = start[:-3]
            start = int(start[-3:])
            stop = int(stop)
            # and expand the range
            cols = [stem + str(col).rjust(3, "0") for col in range(start, stop + 1)]
            outcols.extend(cols)
        else:
            outcols.append(col)
    return outcols


def _normalize_relation(relation):
    parts = relation.split("+")
    if len(parts) == 1:
        if ":" not in relation:
            return relation
        else:
            relation = parts[0]
    else:
        relation = "+".join([_normalize_relation(rel.strip()) for rel in parts])
    if ":" in relation:
        start, stop = relation.split(":")
        stem = start[:-3]
        start = int(start[-3:])
        stop = int(stop)
        # and expand the range
        cols = [stem + str(col).rjust(3, "0") for col in range(start, stop + 1)]
        return "+".join(cols)
    return relation
