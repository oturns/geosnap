import json
import os
import pathlib
import shutil
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


# Status codes worth retrying: rate limiting and transient server errors.
# Everything else (400 bad request, 404, 414 URI-too-long, ...) is a client
# error that will not resolve on retry and must be surfaced immediately.
_RETRIABLE_STATUS = frozenset({429, 500, 502, 503, 504})


def _redact_key(url):
    """Strip the ``key=`` query parameter so the API key never lands in logs."""
    import re

    return re.sub(r"([?&]key=)[^&]*", r"\1***", url)


class Acs5RequestError(RuntimeError):
    """An ACS5 HTTP request returned an error response.

    Carries the HTTP status ``code`` and response ``body`` so callers can
    distinguish, e.g., a "group does not exist" 400 (skip the group) from a
    "request-uri too long" 414 (retry at a finer geography) without re-parsing
    opaque exception strings.
    """

    def __init__(self, message, code=None, body="", url=None):
        super().__init__(message)
        self.code = code
        self.body = body or ""
        self.url = url


def _acs5_request(year, params, session=None, timeout=60, max_retries=6, backoff=1.0, api_key=None):
    """Issue a resilient ACS5 request and return parsed JSON content.

    Uses a persistent ``requests.Session`` for connection reuse when
    ``session`` is provided, which significantly reduces per-request
    overhead during large batch downloads.
    Always includes the API key if provided or available in the environment.

    Transient failures (network errors and the status codes in
    ``_RETRIABLE_STATUS``) are retried with exponential backoff. Non-retriable
    HTTP errors are raised immediately as :class:`Acs5RequestError` carrying the
    status code and body, so a single unavailable table does not burn six
    backoff cycles before failing.
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
        code = None
        body = ""
        try:
            if session is not None:
                resp = session.get(url, timeout=timeout)
                if resp.status_code == 200:
                    return resp.json()
                code, body = resp.status_code, resp.text
            else:
                try:
                    with urlopen(url, timeout=timeout) as resp:
                        return json.loads(resp.read().decode("utf-8"))
                except HTTPError as err:
                    code = err.code
                    body = err.read().decode("utf-8", "ignore")
        except Exception as err:  # network/timeout/JSON-decode: retriable
            last_error = err
        else:
            # We have an HTTP error status (code is set).
            err = Acs5RequestError(
                f"HTTP {code} for {_redact_key(url)}", code=code, body=body, url=url
            )
            if code not in _RETRIABLE_STATUS:
                raise err
            last_error = err

        time.sleep(backoff * (2**attempt))

    raise Acs5RequestError(
        f"ACS5 request failed after {max_retries} attempts: {_redact_key(url)}",
        code=getattr(last_error, "code", None),
        body=getattr(last_error, "body", ""),
        url=url,
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


class GroupUnavailableError(Exception):
    """Raised when a variable group is not tabulated for a given geography/year.

    Not all detailed tables are published at every geographic level (many
    tract-level tables are absent at the block-group level). The API reports
    these with an HTTP 400 "group does not exist" response; treating them as
    skippable rather than fatal lets a national build finish with the tables
    that *are* available.
    """
    pass


def _is_estimate_column(col):
    """Return True if ``col`` is an ACS detailed-table estimate variable.

    Estimate variables end in ``E`` preceded by the (numeric) line number,
    e.g. ``B19013_001E``. This excludes margins (``...M``), annotation columns
    (``...EA``/``...MA``) and the ``NAME``/``GEO_ID`` geography identifiers that
    a ``group()`` query returns alongside the estimates. The published
    ``demographic_profile`` tables are estimates only, so those are all we keep.
    """
    return len(col) > 1 and col.endswith("E") and col[-2].isdigit()


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
    """Download one state/county group chunk and write a lean parquet file.

    The chunk holds only the ``geoid`` and the estimate columns for ``group``.
    ``NAME``, ``GEO_ID``, margins and annotation columns returned by the
    ``group()`` macro are dropped here so the assembled table matches the
    estimates-only ``demographic_profile`` format and chunks never collide on
    shared identifier columns during assembly.

    When ``state_level=True`` the request is issued at the state level
    (e.g. ``for=tract:*&in=state:06``) instead of county level. This reduces the
    total number of API calls by roughly 60×, but may hit Census size limits for
    large states or wide variable groups, in which case
    :class:`StateLevelTooLargeError` is raised so the caller can retry at county
    level.
    """
    # NOTE: do *not* prepend "NAME," to the get list. The group() macro already
    # returns NAME; adding it again yields a duplicate column (NAME / NAME_1).
    params = {"get": f"group({group})"}
    if level == "tract":
        params["for"] = "tract:*"
        # Tracts support a state-scoped query; block groups do not.
        params["in"] = (
            f"state:{state}"
            if state_level
            else f"state:{state} county:{county}"
        )
    elif level == "blockgroup":
        params["for"] = "block group:*"
        # The API rejects "state:XX" alone for block groups ("unknown/unsupported
        # geography hierarchy"); a county is required. Use the county wildcard to
        # still fetch a whole state in one request when state_level is set.
        params["in"] = (
            f"state:{state} county:*"
            if state_level
            else f"state:{state} county:{county}"
        )
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
    except Acs5RequestError as err:
        body = (err.body or "").lower()
        if err.code == 400 and "does not exist" in body:
            raise GroupUnavailableError(
                f"group {group} not available at {level} level for {year}"
            ) from err
        # A single state's response can be too big (URI too long / payload too
        # large / row cap). Retrying the same request will not help, but
        # splitting it into county-level requests will.
        too_large = err.code in (413, 414) or any(
            marker in body
            for marker in ("too large", "too many rows", "request-uri too long")
        )
        if state_level and too_large:
            raise StateLevelTooLargeError(
                f"state-level request too large for {level}|{state}|{group}"
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

    keep = ["geoid"] + [c for c in df.columns if _is_estimate_column(c)]
    df = df[keep]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path)
    return len(df)


def _download_file(url, dest, timeout=120, max_retries=4, backoff=1.0):
    """Stream ``url`` to ``dest`` atomically, retrying transient failures.

    A 404 (the file does not exist, e.g. a territory with no TIGER coverage) is
    raised immediately so the caller can skip it rather than retrying.
    """
    dest = pathlib.Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    last_error = None
    for attempt in range(max_retries):
        try:
            with urlopen(url, timeout=timeout) as resp, open(tmp, "wb") as fh:
                shutil.copyfileobj(resp, fh)
            os.replace(tmp, dest)
            return dest
        except HTTPError as err:
            if err.code == 404:
                raise
            last_error = err
        except Exception as err:
            last_error = err
        time.sleep(backoff * (2**attempt))
    raise RuntimeError(f"failed to download {url}") from last_error


# Detailed TIGER/Line attribute columns to carry alongside geometry. Block group
# files omit NAME; tract files include it. Missing columns are simply skipped.
_TIGER_GEOM_COLS = [
    "GEOID", "STATEFP", "COUNTYFP", "TRACTCE", "BLKGRPCE",
    "NAME", "NAMELSAD", "MTFCC", "FUNCSTAT", "ALAND", "AWATER",
    "INTPTLAT", "INTPTLON", "geometry",
]


def _load_tiger_geometry(
    year, level, states, cache_dir, workers=8, overwrite=False, timeout=120
):
    """Return national TIGER/Line geometry for tracts or block groups.

    The published ``demographic_profile`` tables carry the *detailed* (not
    generalized) TIGER/Line boundaries for each vintage, so this downloads the
    per-state ``tl_{year}_{state}_{tract|bg}.zip`` shapefiles for ``year``,
    concatenates them into one GeoDataFrame keyed on ``GEOID``, and caches the
    result. States without a TIGER file for the level (e.g. some territories)
    are skipped with a warning.
    """
    try:
        import pyogrio
    except ImportError as e:
        raise ImportError(
            "building geometry requires the `pyogrio` package\n"
            "`conda install pyogrio` or pass geometry=False"
        ) from e

    cache_dir = pathlib.Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    token = {"tract": "tract", "blockgroup": "bg"}[level]
    subdir = token.upper()

    combined = cache_dir / f"tiger_{level}_{year}.parquet"
    if combined.exists() and not overwrite:
        return gpd.read_parquet(combined)

    def _one(state):
        url = (
            f"https://www2.census.gov/geo/tiger/TIGER{year}/{subdir}/"
            f"tl_{year}_{state}_{token}.zip"
        )
        zpath = cache_dir / f"tl_{year}_{state}_{token}.zip"
        if overwrite or not zpath.exists():
            try:
                _download_file(url, zpath, timeout=timeout)
            except HTTPError as err:
                if err.code == 404:
                    return None  # no TIGER file for this state/level
                raise
        return pyogrio.read_dataframe(f"/vsizip/{zpath}")

    frames = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_one, s): s for s in states}
        for fut in tqdm(
            as_completed(futures),
            total=len(futures),
            desc=f"TIGER {level} geometry {year}",
        ):
            state = futures[fut]
            try:
                gdf = fut.result()
            except Exception as err:
                warn(f"skipping geometry for state {state}: {err}", stacklevel=2)
                continue
            if gdf is not None and len(gdf):
                frames.append(gdf)

    if not frames:
        raise RuntimeError(f"No TIGER {level} geometry could be downloaded for {year}")

    crs = frames[0].crs
    national = pd.concat(frames, ignore_index=True)
    keep = [c for c in _TIGER_GEOM_COLS if c in national.columns]
    national = gpd.GeoDataFrame(national[keep], geometry="geometry", crs=crs)
    national = national.drop_duplicates(subset=["GEOID"])
    national.to_parquet(combined)
    return national


def _assemble_acs5_chunks(level, year, chunk_dir, output_dir, geometry=None):
    """Assemble per-state/county group chunks into one national wide table.

    Each chunk is reduced to ``geoid`` plus its estimate columns (defensively,
    so chunks written by older versions of :func:`_download_acs5_chunk` that
    still carry ``NAME``/``GEO_ID``/margins are handled too). Because every group
    contributes a disjoint set of estimate columns keyed on ``geoid``, the groups
    are aligned with a single concat rather than a chain of outer joins, and
    columns that are entirely null (tables not tabulated for this geography) are
    dropped to mirror the published ``demographic_profile`` tables.

    When a ``geometry`` GeoDataFrame is supplied (keyed on ``GEOID``) it is joined
    onto the estimates so the output is a GeoDataFrame, matching the published
    tables. Estimate rows without a matching boundary keep a null geometry.
    """
    chunk_dir = pathlib.Path(chunk_dir)
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(chunk_dir.glob("*.parquet"))
    if not files:
        raise RuntimeError("No chunk files were found; nothing to assemble")

    grouped = {}
    for f in files:
        # filename convention: {level}_{state}[_{county}]_{group}.parquet
        grp = f.stem.split("_", 3)[-1]
        grouped.setdefault(grp, []).append(f)

    frames = []
    for _grp, grp_files in tqdm(
        sorted(grouped.items()),
        desc=f"Assembling {level} groups",
    ):
        tables = [pd.read_parquet(p) for p in grp_files]
        frame = pd.concat(tables, axis=0, ignore_index=True)
        est_cols = [c for c in frame.columns if _is_estimate_column(c)]
        if not est_cols:
            continue
        frame = (
            frame[["geoid"] + est_cols]
            .drop_duplicates(subset=["geoid"])
            .set_index("geoid")
        )
        frames.append(frame.apply(pd.to_numeric, errors="coerce"))

    if not frames:
        raise RuntimeError("No estimate columns were found across chunks")

    merged = pd.concat(frames, axis=1, join="outer")
    merged = merged.dropna(axis=1, how="all")
    merged = merged.reset_index().rename(columns={"geoid": "GEOID"})

    if geometry is not None:
        # right-join keeps every estimate row and attaches its boundary
        merged = geometry.merge(merged, on="GEOID", how="right")
        merged = gpd.GeoDataFrame(merged, geometry="geometry", crs=geometry.crs)

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
    geometry=True,
    manifest_interval=50,
    manifest_period=5.0,
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
    geometry : bool, optional
        If True (default), download the detailed TIGER/Line boundaries for the
        matching vintage and join them onto the estimates so the output is a
        GeoDataFrame, matching the published ``demographic_profile`` tables. If
        False, the output is attribute-only, keyed on ``GEOID``.
    api_key : str, optional
        Census API key. If None, falls back to the ``CENSUS`` environment
        variable; if that is also unset, unauthenticated requests are used.
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
    manifest_interval : int, optional
        Maximum number of chunk completions between manifest checkpoints.
        Writing the manifest after every completion serializes workers on
        the GIL (O(N²) total work); batching keeps the GIL free for I/O.
        Default 50.
    manifest_period : float, optional
        Maximum number of seconds between manifest checkpoints. Combined
        with ``manifest_interval`` (whichever triggers first) bounds the
        amount of work lost on a hard crash. Default 5.0.

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

    # Enumerate counties for every state in parallel.  The previous code
    # issued these ~50 requests serially before any chunk downloading
    # could begin, adding ~50× request latency of startup time.
    state_counties = {}
    if not state_level:
        enum_workers = min(8, max(1, len(states)))
        with ThreadPoolExecutor(max_workers=enum_workers) as enum_pool:
            future_to_state = {
                enum_pool.submit(
                    _load_state_counties,
                    year,
                    state,
                    metadata_dir,
                    api_key,
                    overwrite,
                ): state
                for state in states
            }
            for fut in as_completed(future_to_state):
                state_counties[future_to_state[fut]] = fut.result()

    tasks = []
    for state in states:
        if state_level:
            for group in sorted(groups):
                tid = f"{level}|{state}|{group}"
                chunk_name = f"{level}_{state}_{group}.parquet"
                chunk_path = chunks_dir / chunk_name
                tasks.append((tid, state, None, group, chunk_path))
        else:
            for county in state_counties.get(state, []):
                for group in sorted(groups):
                    tid = _task_id(level, state, county, group)
                    chunk_name = f"{level}_{state}_{county}_{group}.parquet"
                    chunk_path = chunks_dir / chunk_name
                    tasks.append((tid, state, county, group, chunk_path))

    manifest_path = cache_root / "manifest.json"
    tmp_manifest_path = manifest_path.with_suffix(".json.tmp")
    completed = set()
    # Groups that the API reports as unavailable for this geography/year. These
    # are recorded so resumed runs don't re-probe them on every pass, but they
    # are not treated as failures.
    skipped = set()
    failed = {}
    if resume and not overwrite:
        # If a temp manifest exists from a previous interrupted run, recover it.
        source = None
        if tmp_manifest_path.exists() and not manifest_path.exists():
            source = tmp_manifest_path
            recovered_msg = "Recovered manifest from interrupted run."
        elif manifest_path.exists():
            source = manifest_path
            recovered_msg = None
        if source is not None:
            try:
                with source.open("r") as f:
                    manifest = json.load(f)
                completed = set(manifest.get("completed", []))
                skipped = set(manifest.get("skipped", []))
                failed = manifest.get("failed", {})
                if recovered_msg:
                    warn(recovered_msg, stacklevel=2)
            except (json.JSONDecodeError, ValueError):
                warn(
                    f"{source.name} is corrupted; starting fresh.",
                    stacklevel=2,
                )
                completed, skipped, failed = set(), set(), {}

    pending = []
    for tid, state, county, group, chunk_path in tasks:
        if not overwrite and resume and (
            tid in completed or tid in skipped or chunk_path.exists()
        ):
            if tid not in skipped:
                completed.add(tid)
            continue
        pending.append((tid, state, county, group, chunk_path))

    _manifest_lock = threading.Lock()

    def _save_manifest():
        # Compact JSON (no indent) and no per-write sort: the manifest is a
        # resumability checkpoint, not a human-readable artifact.  Sorting a
        # 50k–3M-entry set and pretty-printing it on every completion
        # serialized the worker threads on the GIL and collapsed throughput.
        with _manifest_lock:
            tmp_path = manifest_path.with_suffix(".json.tmp")
            with tmp_path.open("w") as f:
                json.dump(
                    {
                        "year": year,
                        "level": level,
                        "tasks_total": len(tasks),
                        "completed": list(completed),
                        "skipped": list(skipped),
                        "failed": failed,
                    },
                    f,
                    separators=(",", ":"),
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
                return ("FALLBACK", state, group)
            except GroupUnavailableError:
                # Table is not tabulated for this geography; skip, don't fail.
                return ("SKIP", state, group)

        # Track fallback tasks to enqueue
        fallback_tasks = []

        # Batched manifest writes: only checkpoint every ``manifest_interval``
        # completions or every ``manifest_period`` seconds.  Writing on every
        # completion re-sorts/re-serializes the whole manifest under the GIL
        # and starves the worker threads.
        completions_since_save = 0
        last_save_time = time.time()

        try:
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
                        if isinstance(result, tuple) and result[0] == "FALLBACK":
                            # Enqueue county-level tasks for this state/group
                            fallback_tasks.append((state, group))
                            failed[tid] = (
                                "State-level request too large, "
                                "will retry at county-level"
                            )
                        elif isinstance(result, tuple) and result[0] == "SKIP":
                            skipped.add(tid)
                            failed.pop(tid, None)
                        else:
                            completed.add(tid)
                            failed.pop(tid, None)
                    except Exception as err:  # pragma: no cover
                        failed[tid] = str(err)

                    completions_since_save += 1
                    now = time.time()
                    if (
                        completions_since_save >= manifest_interval
                        or now - last_save_time >= manifest_period
                    ):
                        _save_manifest()
                        completions_since_save = 0
                        last_save_time = now
        except BaseException:
            # Ensure a checkpoint exists before bubbling up (Ctrl-C, etc.).
            _save_manifest()
            raise
        else:
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

            # Run county-level tasks (batched manifest writes, same as above)
            completions_since_save = 0
            last_save_time = time.time()
            try:
                with ThreadPoolExecutor(max_workers=workers) as pool:
                    futures = {}
                    for tid, state, county, group, chunk_path in county_level_tasks:
                        fut = pool.submit(
                            _worker, state, county, group, chunk_path, False
                        )
                        futures[fut] = tid

                    for fut in tqdm(
                        as_completed(futures),
                        total=len(futures),
                        desc=f"Fallback county-level {level}",
                    ):
                        tid = futures[fut]
                        try:
                            result = fut.result()
                            if isinstance(result, tuple) and result[0] == "SKIP":
                                skipped.add(tid)
                                failed.pop(tid, None)
                            else:
                                completed.add(tid)
                                failed.pop(tid, None)
                        except Exception as err:
                            failed[tid] = str(err)

                        completions_since_save += 1
                        now = time.time()
                        if (
                            completions_since_save >= manifest_interval
                            or now - last_save_time >= manifest_period
                        ):
                            _save_manifest()
                            completions_since_save = 0
                            last_save_time = now
            except BaseException:
                _save_manifest()
                raise
            else:
                _save_manifest()

    # Assemble whatever completed rather than discarding a large national
    # download because a handful of chunks failed. Genuinely-failed chunks are
    # surfaced as a warning; re-running with resume=True retries only those.
    if failed:
        warn(
            f"{len(failed)} chunk download(s) failed and were omitted from the "
            f"assembled table. Re-run with resume=True to retry them. "
            f"First few: {list(failed)[:5]}",
            stacklevel=2,
        )
    if skipped:
        warn(
            f"{len(skipped)} group/geography combination(s) were unavailable "
            "from the API and skipped.",
            stacklevel=2,
        )

    geom = None
    if geometry:
        geom = _load_tiger_geometry(
            year,
            level,
            states,
            cache_root / "geometry",
            workers=workers,
            overwrite=overwrite,
            timeout=timeout,
        )

    return _assemble_acs5_chunks(
        level, year, chunks_dir, output_dir, geometry=geom
    )


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
