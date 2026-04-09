from __future__ import annotations
import os
import sys
from pathlib import Path
import geopandas as gpd
import requests
from github import Github

from geosnap.io.util import get_census_gdb, convert_census_gdb, process_acs
REPO = "oturns/geosnap"
ISSUE_PREFIX = "New ACS release detected:"
CENSUS_ROOT = "https://www2.census.gov/geo/tiger/TIGER_DP"
TIMEOUT = 30

# TODO: make this update dynamically
LATEST_SUPPORTED_YEAR = 2021

# Start with one geography to keep memory lower and behavior predictable.
GEOM_LEVEL = "blockgroup"  # "blockgroup" or "tract"
LEVEL_CODE = "bg" if GEOM_LEVEL == "blockgroup" else "tract"
FILE_SUFFIX = "BG" if GEOM_LEVEL == "blockgroup" else "TRACT"

# ensure the file actually has stuff in it
MIN_EXPECTED_SIZE_BYTES = 1_250_000_000

WORKDIR = Path("build") / f"{LATEST_SUPPORTED_YEAR + 1}_{LEVEL_CODE}"


def census_year_url(year: int) -> str:
    return f"{CENSUS_ROOT}/{year}ACS/"


def expected_file(year: int) -> str:
    return f"ACS_{year}_5YR_{FILE_SUFFIX}.gdb.zip"


def expected_file_url(year: int) -> str:
    return f"{census_year_url(year)}{expected_file(year)}"


def fetch_directory_listing(year: int) -> str | None:
    url = census_year_url(year)
    resp = requests.get(url, timeout=TIMEOUT)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.text


def remote_file_size_bytes(url: str) -> int | None:
    """
    Try to get the remote file size from HTTP headers.

    Returns:
        int: size in bytes if available
        None: if the server does not provide Content-Length
    """
    resp = requests.head(url, allow_redirects=True, timeout=TIMEOUT)

    if resp.status_code == 404:
        return None

    # Some servers do not return Content-Length on HEAD. Fall back to GET stream.
    if resp.ok:
        content_length = resp.headers.get("Content-Length")
        if content_length is not None:
            return int(content_length)

    resp = requests.get(url, stream=True, allow_redirects=True, timeout=TIMEOUT)

    if resp.status_code == 404:
        return None

    resp.raise_for_status()
    content_length = resp.headers.get("Content-Length")
    if content_length is None:
        return None
    return int(content_length)


def census_release_status(year: int) -> tuple[bool, str]:
    """
    Check whether the release is ready for processing.

    A release is considered ready only if the year directory exists,
    the expected file is listed in the directory, and the remote
    file size is at least MIN_EXPECTED_SIZE_BYTES
    """
    html = fetch_directory_listing(year)
    if html is None:
        return False, f"{census_year_url(year)} not found"

    filename = expected_file(year)
    if filename not in html:
        return False, f"{filename} not listed in {census_year_url(year)}"

    file_url = expected_file_url(year)
    size_bytes = remote_file_size_bytes(file_url)

    if size_bytes is None:
        return False, f"Could not determine remote file size for {file_url}"

    if size_bytes < MIN_EXPECTED_SIZE_BYTES:
        return (
            False,
            f"{filename} is present but too small "
            f"({size_bytes:,} bytes < {MIN_EXPECTED_SIZE_BYTES:,} bytes)",
        )

    return (
        True,
        f"{filename} is present and large enough "
        f"({size_bytes:,} bytes >= {MIN_EXPECTED_SIZE_BYTES:,} bytes)",
    )


def issue_exists(year: int) -> bool:
    query = f'repo:{REPO} is:issue is:open "{ISSUE_PREFIX} {year}"'
    gh = Github(os.environ["GITHUB_TOKEN"])
    return gh.search_issues(query).totalCount > 0


def open_issue(year: int, body: str) -> None:
    gh = Github(os.environ["GITHUB_TOKEN"])
    repo = gh.get_repo(REPO)
    repo.create_issue(
        title=f"{ISSUE_PREFIX} {year}",
        body=body,
    )


def ensure_workdir() -> None:
    WORKDIR.mkdir(parents=True, exist_ok=True)


def download_raw_gdb(year: int) -> Path:
    ensure_workdir()
    get_census_gdb(
        years=[year],
        geom_level=GEOM_LEVEL,
        output_dir=str(WORKDIR),
        protocol="https",
    )
    return WORKDIR / expected_file(year)


def convert_raw_gdb(year: int, gdb_path: Path) -> Path:
    convert_census_gdb(
        year=str(year),
        level=LEVEL_CODE,
        gdb_path=str(gdb_path),
        layers=None,
        save_intermediate=True,
        overwrite=False,
        combine=True,
        output_dir=str(WORKDIR),
    )
    return WORKDIR / f"acs_demographic_profile_{year}_{LEVEL_CODE}.parquet"


def build_processed_acs(year: int, combined_path: Path) -> Path:
    df = gpd.read_parquet(combined_path)

    if "GEOID" not in df.columns:
        df = df.reset_index()

    processed = process_acs(df)

    out_path = WORKDIR / f"acs_{year}_{LEVEL_CODE}.parquet"
    processed.to_parquet(out_path)
    return out_path


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Missing GITHUB_TOKEN", file=sys.stderr)
        return 1

    year = LATEST_SUPPORTED_YEAR + 1

    ready, status_message = census_release_status(year)
    print(status_message)

    if not ready:
        print(f"{year} release not ready for processing.")
        return 0

    try:
        gdb_path = download_raw_gdb(year)
        print(f"Downloaded: {gdb_path}")

        combined_path = convert_raw_gdb(year, gdb_path)
        print(f"Combined parquet: {combined_path}")

        final_path = build_processed_acs(year, combined_path)
        print(f"Processed ACS parquet: {final_path}")

        return 0

        except Exception as exc:
        msg = (
            f"Detected Census ACS release for {year}, but automated processing failed.\n\n"
            f"Checked directory: {census_year_url(year)}\n"
            f"Checked file: {expected_file_url(year)}\n\n"
            f"Preflight check: {status_message}\n\n"
            f"Error:\n```\n{exc}\n```"
        )
        print(msg, file=sys.stderr)

        if os.environ.get("DISABLE_GITHUB_ISSUES", "").lower() not in {"1", "true", "yes"}:
            if not issue_exists(year):
                open_issue(year, msg)
        else:
            print("Skipping issue creation because DISABLE_GITHUB_ISSUES is set.", file=sys.stderr)

        return 1

if __name__ == "__main__":
    raise SystemExit(main())
