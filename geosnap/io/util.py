import json
import os
import pathlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen
from warnings import warn

import geopandas as gpd
import pandas as pd
import pooch
import requests
from tqdm.auto import tqdm


def get_census_gdb(years=None, geom_level="blockgroup", output_dir=".", protocol="ftp"):
    """Fetch geodatabase of ACS demographic profile from the Census bureau server.

    NOTE: Recommended to use `convert_census_gdb` to read/convert files directly from
    the Census server


    Parameters
    ----------
    years : list, optional
        set of years to download (2010 onward), defaults to 2010-2019
    geom_level : str, optional
        geographic unit to download (tract or blockgroup), by default "blockgroup"
    output_dir : str, optional
        output directory to write files, by default "."
    protocol:
        whether to download over ftp or http. ftp is generally more reliable

    Returns
    -------
    None
    """
    levels = {"blockgroup": "bg", "tract": "tract"}

    if not years:
        years = range(2010, 2020)
    for year in years:
        fn = f"ACS_{year}_5YR_{levels[geom_level].upper()}.gdb.zip"
        pth = pathlib.PurePath(output_dir, fn)

        if year in [2010, 2011]:
            if geom_level == "blockgroup":
                raise ValueError(f"blockgroup data not available for {year}") from None
            fn = f"{year}_ACS_5YR_{geom_level.capitalize()}.gdb.zip"
            out_fn = f"ACS_{year}_5YR_{levels[geom_level].upper()}.gdb.zip"
            pth = pathlib.PurePath(output_dir, out_fn)
        urls = {
            "ftp": f"ftp://ftp2.census.gov/geo/tiger/TIGER_DP/{year}ACS/{fn}",
            "https": f"https://www2.census.gov/geo/tiger/TIGER_DP/{year}ACS/{fn}",
        }
        if protocol not in urls:
            raise ValueError("`protocol` must be either 'https' or 'ftp'")
        pooch.retrieve(urls[protocol], None, progressbar=True, fname=fn, path=pth)


def reformat_acs_vars(col):
    """Convert variable names to the same format used by the Census Detailed Tables API.

    See <https://api.census.gov/data/2019/acs/acs5/variables.html> for variable descriptions


    Parameters
    ----------
    col : str
        column name to adjust

    Returns
    -------
    str
        reformatted column name
    """
    pieces = col.split("e")
    formatted = pieces[0] + "_" + pieces[1].rjust(3, "0") + "E"
    return formatted


def convert_census_gdb(
    year,
    level,
    gdb_path=None,
    layers=None,
    save_intermediate=True,
    overwrite=False,
    combine=True,
    output_dir=".",
    npartitions=16,
):
    """Convert a geodatabase from Census into parquet files with standardized columns.

    Parameters
    ----------

    year : str, required
        year that the data should be named by. If none, will try to infer from the
        filename
        based on convention from the Census Bureau FTP server
    level : str, required
        geographic level of data ('bg' for blockgroups or 'tr' for tract),
        path to file geodatabase
    layers : list, optional
        set of layers to extract from geodatabase. If none (default), all layers will be
        extracted
    gdf_path: str
        path to geodatabase. If none is provided, data will be read directly from the
        Census server at <https://www2.census.gov/geo/tiger/TIGER_DP/>
    save_intermediate : bool, optional
        if true, each layer will be stored separately as a parquet file, by default True
    overwrite: bool
        whether to overwrite existing intermediate files in the output directory
        (default is False)
    combine : bool, optional
        whether to store and concatenate intermediate dataframes, default is True.
        If True, the combined file will be stored as
    output_dir : str, optional
        path to directory where parquet files will be written, by default "."

    Returns
    -------
    None
        If save_intermediate is True, parquet files will be written out for each layer in
        the output directory. If combined is True, the layers will be concatenated and
        the resulting dataframe  f"acs_demographic_profile_{year}_{level}.parquet" will
        be placed in the output directory.
    """
    try:
        import pyogrio as ogr
    except ImportError as e:
        raise Exception(
            "This function requires the `pyogrio` package\n`conda install pyogrio`"
        ) from e
    import dask_geopandas as dgpd

    if gdb_path is None:
        warn(
            "No `gdb_path` given. Data will be pulled from the Census server",
            stacklevel=2,
        )
        gdb_path = f"https://www2.census.gov/geo/tiger/TIGER_DP/{year}ACS/ACS_{year}_5YR_{level.upper()}.gdb.zip"
    if layers is None:  # grab them all except the metadata
        year_suffix = year[-2:]
        meta_str = f"{level.upper()}_METADATA_20{year_suffix}"
        layers = [layer[0] for layer in ogr.list_layers(gdb_path)]
        if meta_str in layers:
            layers.remove(meta_str)

    tables = list()
    existing_files = os.listdir(output_dir)
    for i in tqdm(layers):
        print(i)

        output_fn = f"acs_{year}_{i}_{level}.parquet"
        if output_fn in existing_files and overwrite is False:
            warn(
                (
                    f"layer {i} is already present in the output directory. "
                    "To overwrite, pass `overwrite=True`"
                ),
                stacklevel=2,
            )
            if combine:
                if "ACS_" in i:  # only the geoms have the ACS prefix
                    # need to read in with geopandas to get the geoms
                    df = gpd.read_parquet(pathlib.PurePath(output_dir, output_fn))
                else:
                    df = pd.read_parquet(pathlib.PurePath(output_dir, output_fn))
                    df.index = df.index.str.replace("14000US", "")  # remove prefix
                    df.index = df.index.str.replace(
                        "15000US", ""
                    )  # remove prefix for bgs
                tables.append(df)
        else:
            df = (
                dgpd.read_file(gdb_path, layer=i, npartitions=npartitions)
                .compute()
                .set_index("GEOID")
            )
            if "ACS_" not in i:  # only the geoms have the ACS prefix
                df = df[df.columns[df.columns.str.contains("e")]]
                df.columns = pd.Series(df.columns).apply(reformat_acs_vars)
            df = df.dropna(axis=1, how="all")
            df.index = df.index.str.replace("14000US", "")  # remove prefix for tracts
            df.index = df.index.str.replace("15000US", "")  # remove prefix for bgs
            if combine:
                tables.append(df)
            if save_intermediate:
                df.to_parquet(pathlib.PurePath(output_dir, output_fn))
    if combine:
        df = pd.concat(tables, axis=1)
        df = gpd.GeoDataFrame(df)
        df.to_parquet(
            pathlib.PurePath(
                output_dir, f"acs_demographic_profile_{year}_{level}.parquet"
            )
        )


def _acs5_request(year, params, session=None, timeout=60, max_retries=6, backoff=1.0, api_key=None):
    """Issue a resilient ACS5 request and return parsed JSON content.

    Uses a persistent ``requests.Session`` for connection reuse when
    ``session`` is provided, which significantly reduces per-request
    overhead during large batch downloads.
    Always includes the API key if provided or available in the environment.
    """
    # Always add API key if provided or available in env
    if api_key is None:
        api_key = os.environ.get("CENSUS")
    if api_key:
        params = dict(params)  # avoid mutating caller's dict
        params["key"] = api_key
    base = f"https://api.census.gov/data/{year}/acs/acs5"
    query = urlencode(params, safe="*():,")
    url = f"{base}?{query}"

    last_error = None
    for attempt in range(max_retries):
        try:
            if session is not None:
                resp = session.get(url, timeout=timeout)
                resp.raise_for_status()
                return resp.json()
            else:
                with urlopen(url, timeout=timeout) as resp:
                    payload = resp.read().decode("utf-8")
                return json.loads(payload)
        except HTTPError as err:
            last_error = err
            if err.code not in (429, 500, 502, 503, 504):
                raise
        except Exception as err:  # pragma: no cover
            last_error = err
        sleep_for = backoff * (2**attempt)
        time.sleep(sleep_for)

    raise RuntimeError(
        f"ACS5 request failed after {max_retries} attempts: {url}"
    ) from last_error


def _load_acs5_variable_groups(year, cache_dir, overwrite=False):
    """Fetch ACS5 variables metadata and return group->variable list mapping."""
    cache_dir = pathlib.Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    out_path = cache_dir / f"acs5_variables_{year}.json"

    if out_path.exists() and not overwrite:
        with out_path.open("r") as f:
            payload = json.load(f)
    else:
        vars_url = f"https://api.census.gov/data/{year}/acs/acs5/variables.json"
        with urlopen(vars_url) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        with out_path.open("w") as f:
            json.dump(payload, f)

    variables = payload.get("variables", {})
    groups = {}
    for name, meta in variables.items():
        grp = meta.get("group")
        if not grp:
            continue
        if meta.get("predicateOnly"):
            continue
        # Include estimate, MOE, annotations, percent estimates and associated MOEs.
        if not (
            name.endswith("E")
            or name.endswith("M")
            # or name.endswith("EA")
            # or name.endswith("MA")
            # or name.endswith("PE")
            # or name.endswith("PM")
            # or name.endswith("PEA")
            # or name.endswith("PMA")
        ):
            continue
        groups.setdefault(grp, []).append(name)

    for grp in groups:
        groups[grp] = sorted(groups[grp])

    return groups


def _load_states_fips():
    this_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
    st = pd.read_csv(this_dir / "stfipstable.csv", dtype={"FIPS Code": str})
    return sorted(st["FIPS Code"].str.zfill(2).unique().tolist())


def _load_state_counties(year, state_fips, cache_dir, api_key=None, overwrite=False):
    """Return county FIPS codes for a state, cached for resumable runs."""
    cache_dir = pathlib.Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"counties_{state_fips}.json"

    if path.exists() and not overwrite:
        with path.open("r") as f:
            return json.load(f)

    params = {
        "get": "NAME",
        "for": "county:*",
        "in": f"state:{state_fips}",
    }
    if api_key:
        params["key"] = api_key

    try:
        rows = _acs5_request(year, params, api_key=api_key)
    except Exception as err:
        # Some legacy FIPS codes in the local lookup table are not valid
        # ACS geographies.
        warn(
            (
                f"Skipping state FIPS {state_fips}: unable to fetch county list "
                f"from ACS5 ({err})"
            ),
            stacklevel=2,
        )
        return []

    counties = [r[2] for r in rows[1:]]

    with path.open("w") as f:
        json.dump(counties, f)
    return counties


def _task_id(level, state, county, group):
    return f"{level}|{state}|{county}|{group}"


def _deduplicate_columns(columns):
    """
    Ensure all column names are unique by appending _1, _2, ... to duplicates.
    Returns a new list of unique column names.
    """
    counts = {}
    result = []
    for col in columns:
        if col not in counts:
            counts[col] = 0
            result.append(col)
        else:
            counts[col] += 1
            result.append(f"{col}_{counts[col]}")
    return result


class StateLevelTooLargeError(Exception):
    """Raised when a state-level ACS5 request fails due to size/row limits."""
    pass

def _download_acs5_chunk(
    year,
    level,
    state,
    county,
    group,
    out_path,
    api_key=None,
    session=None,
    timeout=60,
    max_retries=6,
    backoff=1.0,
    state_level=False,
):
    """Download one county/group chunk and write a parquet file.

    When ``state_level=True`` the request is issued at the state level
    (e.g. ``for=tract:*&in=state:06``) instead of county level.  This
    reduces the total number of API calls by roughly 60×, but may hit
    Census row limits for large states or wide variable groups.
    """
    params = {
        "get": f"NAME,group({group})",
    }
    if level == "tract":
        params["for"] = "tract:*"
        if state_level:
            params["in"] = f"state:{state}"
        else:
            params["in"] = f"state:{state} county:{county}"
    elif level == "blockgroup":
        params["for"] = "block group:*"
        if state_level:
            params["in"] = f"state:{state}"
        else:
            params["in"] = f"state:{state} county:{county}"
    else:
        raise ValueError("level must be 'tract' or 'blockgroup'")

    if api_key:
        params["key"] = api_key

    try:
        rows = _acs5_request(
            year,
            params,
            session=session,
            timeout=timeout,
            max_retries=max_retries,
            backoff=backoff,
            api_key=api_key,
        )
    except Exception as err:
        # Detect likely state-level size/row limit errors
        if state_level and (
            "too many rows" in str(err).lower()
            or "413" in str(err)
            or "414" in str(err)
            or "request entity too large" in str(err).lower()
            or "request-uri too long" in str(err).lower()
        ):
            raise StateLevelTooLargeError(
                f"State-level request failed for {level}|{state}|{group}: {err}"
            ) from err
        raise

    if len(rows) <= 1:
        return 0

    columns = _deduplicate_columns(rows[0])
    df = pd.DataFrame(rows[1:], columns=columns)
    if level == "tract":
        df["geoid"] = df["state"] + df["county"] + df["tract"]
    else:
        df["geoid"] = df["state"] + df["county"] + df["tract"] + df["block group"]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path)
    return len(df)


def _assemble_acs5_chunks(level, year, chunk_dir, output_dir):
    """Assemble county/group chunks into one national wide table."""
    chunk_dir = pathlib.Path(chunk_dir)
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(chunk_dir.glob("*.parquet"))
    if not files:
        raise RuntimeError("No chunk files were found; nothing to assemble")

    grouped = {}
    for f in files:
        # filename convention: level_state_county_group.parquet
        stem = f.stem
        grp = stem.split("_", 3)[-1]
        grouped.setdefault(grp, []).append(f)

    merged = None
    geom_cols = ["geoid", "NAME", "state", "county", "tract"]
    if level == "blockgroup":
        geom_cols.append("block group")

    for _grp, grp_files in tqdm(
        sorted(grouped.items()),
        desc=f"Assembling {level} groups",
    ):
        tables = [pd.read_parquet(p) for p in grp_files]
        frame = pd.concat(tables, axis=0, ignore_index=True)
        frame = frame.drop_duplicates(subset=["geoid"]).set_index("geoid")

        for col in frame.columns:
            if col in geom_cols:
                continue
            frame[col] = pd.to_numeric(frame[col], errors="coerce")

        if merged is None:
            merged = frame
            continue

        keep = [c for c in frame.columns if c not in geom_cols or c == "geoid"]
        merged = merged.join(frame[keep], how="outer")

    merged = merged.reset_index().rename(columns={"geoid": "GEOID"})
    out = output_dir / f"acs_demographic_profile_{year}_{level}.parquet"
    merged.to_parquet(out)
    return out


def convert_census_acs5(
    year,
    level,
    output_dir=".",
    api_key=None,
    workers=8,
    overwrite=False,
    resume=True,
    timeout=60,
    max_retries=6,
    backoff=1.0,
    state_level=False,
):
    """Build a national ACS5 demographic profile table from ACS5 API detail tables only.

    Parameters
    ----------
    year : int or str
        ACS5 year to download.
    level : str
        Geographic level: "tract" or "blockgroup".
    output_dir : str, optional
        Directory for cache artifacts and final parquet output.
    api_key : str, optional
        Census API key. If None, unauthenticated requests are used.
    workers : int, optional
        Number of concurrent county/group request workers.
    overwrite : bool, optional
        If True, ignore existing chunk and metadata cache files.
    resume : bool, optional
        If True, skip completed chunk tasks according to manifest/chunk files.
    timeout : int, optional
        HTTP request timeout in seconds.
    max_retries : int, optional
        Maximum retries per request on transient errors.
    backoff : float, optional
        Base exponential backoff interval.
    state_level : bool, optional
        If True, request data at the state level instead of county level.
        This reduces API calls by ~60× but may hit Census row limits for
        large states or wide variable groups. Default is False (county level).

    Returns
    -------
    pathlib.Path
        Path to output parquet file.
    """

    year = str(year)
    aliases = {"bg": "blockgroup", "block group": "blockgroup", "tr": "tract"}
    level = aliases.get(level, level)
    if level not in {"tract", "blockgroup"}:
        raise ValueError("level must be one of {'tract', 'blockgroup', 'bg', 'tr'}")

    # Always set api_key from environment if not provided
    if api_key is None:
        api_key = os.environ.get("CENSUS")

    output_dir = pathlib.Path(output_dir)
    cache_root = output_dir / ".acs5_cache" / year / level
    chunks_dir = cache_root / "chunks"
    metadata_dir = output_dir / ".acs5_cache" / year / "metadata"
    cache_root.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    groups = _load_acs5_variable_groups(year, metadata_dir, overwrite=overwrite)
    states = _load_states_fips()

    tasks = []
    for state in states:
        if state_level:
            for group in sorted(groups):
                tid = f"{level}|{state}|{group}"
                chunk_name = f"{level}_{state}_{group}.parquet"
                chunk_path = chunks_dir / chunk_name
                tasks.append((tid, state, None, group, chunk_path))
        else:
            counties = _load_state_counties(
                year,
                state,
                metadata_dir,
                api_key=api_key,
                overwrite=overwrite,
            )
            for county in counties:
                for group in sorted(groups):
                    tid = _task_id(level, state, county, group)
                    chunk_name = f"{level}_{state}_{county}_{group}.parquet"
                    chunk_path = chunks_dir / chunk_name
                    tasks.append((tid, state, county, group, chunk_path))

    manifest_path = cache_root / "manifest.json"
    tmp_manifest_path = manifest_path.with_suffix(".json.tmp")
    completed = set()
    failed = {}
    if resume and not overwrite:
        # If a temp manifest exists from a previous interrupted run, recover it.
        if tmp_manifest_path.exists() and not manifest_path.exists():
            try:
                with tmp_manifest_path.open("r") as f:
                    manifest = json.load(f)
                completed = set(manifest.get("completed", []))
                failed = manifest.get("failed", {})
                warn(
                    "Recovered manifest from interrupted run.",
                    stacklevel=2,
                )
            except (json.JSONDecodeError, ValueError):
                warn(
                    "Temp manifest is corrupted; starting fresh.",
                    stacklevel=2,
                )
                completed = set()
                failed = {}
        elif manifest_path.exists():
            try:
                with manifest_path.open("r") as f:
                    manifest = json.load(f)
                completed = set(manifest.get("completed", []))
                failed = manifest.get("failed", {})
            except (json.JSONDecodeError, ValueError):
                warn(
                    "Manifest file is corrupted; starting fresh.",
                    stacklevel=2,
                )
                completed = set()
                failed = {}

    pending = []
    for tid, state, county, group, chunk_path in tasks:
        if not overwrite and resume and (tid in completed or chunk_path.exists()):
            completed.add(tid)
            continue
        pending.append((tid, state, county, group, chunk_path))

    _manifest_lock = threading.Lock()

    def _save_manifest():
        with _manifest_lock:
            tmp_path = manifest_path.with_suffix(".json.tmp")
            with tmp_path.open("w") as f:
                json.dump(
                    {
                        "year": year,
                        "level": level,
                        "tasks_total": len(tasks),
                        "completed": sorted(completed),
                        "failed": failed,
                    },
                    f,
                    indent=2,
                )
            os.replace(tmp_path, manifest_path)

    _save_manifest()

    if pending:
        _local = threading.local()

        def _get_session():
            if getattr(_local, "session", None) is None:
                _local.session = requests.Session()
            return _local.session

        def _worker(state, county, group, chunk_path, state_level_flag=True):
            try:
                return _download_acs5_chunk(
                    year,
                    level,
                    state,
                    county,
                    group,
                    chunk_path,
                    api_key=api_key,
                    session=_get_session(),
                    timeout=timeout,
                    max_retries=max_retries,
                    backoff=backoff,
                    state_level=state_level_flag,
                )
            except StateLevelTooLargeError:
                # Fallback: enqueue county-level tasks for this state/group
                return "FALLBACK", state, group

        # Track fallback tasks to enqueue
        fallback_tasks = []

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {}
            for tid, state, county, group, chunk_path in pending:
                fut = pool.submit(
                    _worker, state, county, group, chunk_path, state_level
                )
                futures[fut] = (tid, state, county, group, chunk_path)

            for fut in tqdm(
                as_completed(futures),
                total=len(futures),
                desc=f"Downloading {level}",
            ):
                tid, state, county, group, chunk_path = futures[fut]
                try:
                    result = fut.result()
                    if result == "FALLBACK":
                        # Enqueue county-level tasks for this state/group
                        fallback_tasks.append((state, group))
                        failed[tid] = (
                            "State-level request too large, will retry at county-level"
                        )
                    else:
                        completed.add(tid)
                        if tid in failed:
                            del failed[tid]
                except Exception as err:  # pragma: no cover
                    failed[tid] = str(err)
                _save_manifest()

        # Handle fallback tasks (county-level for failed state/group)
        if fallback_tasks:
            # Remove failed state-level tasks from completed/failed
            for state, group in fallback_tasks:
                tid = f"{level}|{state}|{group}"
                if tid in completed:
                    completed.remove(tid)
                if tid in failed:
                    del failed[tid]

            # Build new county-level tasks for each failed state/group
            county_level_tasks = []
            for state, group in fallback_tasks:
                counties = _load_state_counties(
                    year,
                    state,
                    metadata_dir,
                    api_key=api_key,
                    overwrite=overwrite,
                )
                for county in counties:
                    tid = _task_id(level, state, county, group)
                    chunk_name = f"{level}_{state}_{county}_{group}.parquet"
                    chunk_path = chunks_dir / chunk_name
                    if (
                        not overwrite
                        and resume
                        and (tid in completed or chunk_path.exists())
                    ):
                        completed.add(tid)
                        continue
                    county_level_tasks.append((tid, state, county, group, chunk_path))

            # Run county-level tasks
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {}
                for tid, state, county, group, chunk_path in county_level_tasks:
                    fut = pool.submit(_worker, state, county, group, chunk_path, False)
                    futures[fut] = tid

                for fut in tqdm(
                    as_completed(futures),
                    total=len(futures),
                    desc=f"Fallback county-level {level}",
                ):
                    tid = futures[fut]
                    try:
                        fut.result()
                        completed.add(tid)
                        if tid in failed:
                            del failed[tid]
                    except Exception as err:
                        failed[tid] = str(err)
                    _save_manifest()

    if failed:
        raise RuntimeError(
            f"{len(failed)} chunk downloads failed. "
            "Re-run with resume=True to retry unfinished work."
        )

    return _assemble_acs5_chunks(level, year, chunks_dir, output_dir)


def adjust_inflation(df, columns, given_year, base_year):
    """
    Adjust currency data for inflation.

    Parameters
    ----------
    df : DataFrame
        Dataframe of historical data
    columns : list-like
        The columns of the dataframe with currency data
    given_year: int
        The year in which the data were collected; e.g. to convert data from
        the 1990 census to 2015 dollars, this value should be 1990.
    base_year: int, optional
        Constant dollar year; e.g. to convert data from the 1990
        census to constant 2015 dollars, this value should be 2015.
        Default is 2015.

    Returns
    -------
    type
        DataFrame
    """

    coef = _get_inflate_coef(given_year, base_year)
    for col in columns:
        df[col] = df[col] * coef
    return df


def get_lehd(dataset="wac", state="dc", year=2015, version=8):
    """Grab data from the LODES FTP server as a pandas DataFrame.

    Parameters
    ----------
    dataset : str
        which LODES dataset to collect: "rac" or wac", reffering to either
        residence area characteristics or workplace area characteristics
        the default is 'wac').
    state : str
        two-digit state abbreviation for example "ca" or "OH"
    year : str
        which year to collect. First year avaialable for most states is 2002.
        Consult the LODES documentation for more details. The default is 2015.
    version : int
        which version of LODES to query. Options include 5,7 and 8, which are keyed
        to census 2000, 2010, and 2020 blocks respectively

    Returns
    -------
    pandas.DataFrame
        a pandas DataFrame with columns representing census blocks, indexed on
        the block FIPS code.

    """
    lodes_vars = pd.read_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "lodes.csv")
    )
    renamer = dict(zip(lodes_vars["variable"].tolist(), lodes_vars["name"].tolist()))

    state = state.lower()
    url = f"https://lehd.ces.census.gov/data/lodes/LODES{version}/{state}/{dataset}/{state}_{dataset}_S000_JT00_{year}.csv.gz"
    try:
        df = pd.read_csv(url, converters={"w_geocode": str, "h_geocode": str})
    except HTTPError as e:
        raise ValueError(
            "Unable to retrieve LEHD data. Check your internet connection "
            "and that the state/year combination you specified is available"
        ) from e
    df = df.rename({"w_geocode": "geoid", "h_geocode": "geoid"}, axis=1)
    df.rename(renamer, axis="columns", inplace=True)
    df = df.set_index("geoid")

    return df


def _get_inflate_coef(given_year, base_year):
    """
    Adjust currency data for inflation.

    Parameters
    ----------
    given_year: int
        The year in which the data were collected; e.g. to convert data from
        the 1990 census to 2015 dollars, this value should be 1990.
    base_year: int, optional
        Constant dollar year; e.g. to convert data from the 1990
        census to constant 2015 dollars, this value should be 2015.
        Default is 2015.

    Returns
    -------
    type
        float

    """

    inflation = pd.read_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "inflation.csv"),
        skiprows=5,
    )
    inflation.columns = inflation.columns.str.lower()
    inflation.columns = inflation.columns.str.strip(".")
    inflation = inflation.dropna(subset=["year"])
    inflator = inflation.groupby("year")["avg"].first().to_dict()
    inflator[1970] = 63.9

    for year in [given_year, base_year]:
        if year not in inflator:
            raise ValueError(
                f"{year} not available in inflation data. Check online at <https://www.bls.gov/cpi/research-series/r-cpi-u-rs-allitems.xlsx>"
            )

    return inflator[base_year] / inflator[given_year]


def process_acs(df):
    """Calculate variables from the geosnap codebook to match the LTDB veriable set.

    This function expects a massive input dataframe generated by downloading all
    necessary varibales from the geosnap codebook. The best way to get all these
    variables is to use the `geosnap.io.process_census_gdb` function. Note that
    calling this function on the full dataset requires *a lot* of memory.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame contining raw census data (as processed by `fetch_acs`).
        (expects GEOID as a column, not as index)

    Returns
    -------
    geopandas.GeoDataFrame
        a geodataframe holding
    """
    from .._data import DataStore

    geoms = df["geometry"].copy()

    _variables = pd.read_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "variables.csv")
    )

    evalcols = [_normalize_relation(rel) for rel in _variables["acs"].dropna().tolist()]
    varnames = _variables.dropna(subset=["acs"])["variable"]
    evals = [parts[0] + "=" + parts[1] for parts in zip(varnames, evalcols)]

    tempkeeps = [col for col in df.columns if col in evalcols]
    df = df[tempkeeps + ["geometry", "GEOID"]]
    df.set_index("GEOID", inplace=True)
    df = df.apply(lambda x: pd.to_numeric(x, errors="coerce"), axis=1)
    # compute additional variables from lookup table
    for row in tqdm(evals):
        try:
            df.eval(row, inplace=True)
        except Exception as e:
            print(row + " " + str(e))
    for row in _variables["formula"].dropna().tolist():
        try:
            df.eval(row, inplace=True, engine="python")
        except Exception as e:
            print(str(row) + " " + str(e))
    keeps = [col for col in df.columns if col in _variables.variable.tolist()]
    df = df[keeps]
    df["geometry"] = geoms.values
    df = gpd.GeoDataFrame(df)
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


if __name__ == "__main__":
    get_lehd()
    adjust_inflation()
