from __future__ import annotations

import os
import sys
import requests
from github import Github

REPO = "oturns/geosnap"
ISSUE_PREFIX = "New ACS release detected:"
CENSUS_ROOT = "https://www2.census.gov/geo/tiger/TIGER_DP"
TIMEOUT = 30

# Temporary until this can be inferred from package metadata or datastore contents
LATEST_SUPPORTED_YEAR = 2021

def census_year_url(year: int) -> str:
    return f"{CENSUS_ROOT}/{year}ACS/"

def expected_files(year: int) -> list[str]:
    # block group + tract are the most relevant sentinels for geosnap's tooling
    return [
        f"ACS_{year}_5YR_BG.gdb.zip",
        f"ACS_{year}_5YR_TRACT.gdb.zip",
    ]

def fetch_directory_listing(year: int) -> str | None:
    url = census_year_url(year)
    resp = requests.get(url, timeout=TIMEOUT)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.text

def census_release_ready(year: int) -> tuple[bool, list[str]]:
    html = fetch_directory_listing(year)
    if html is None:
        return False, []
    missing = [name for name in expected_files(year) if name not in html]
    return len(missing) == 0, missing

def issue_exists(repo, year: int) -> bool:
    query = f'repo:{REPO} is:issue is:open "{ISSUE_PREFIX} {year}"'
    return Github(os.environ["GITHUB_TOKEN"]).search_issues(query).totalCount > 0

def open_issue(repo, year: int, missing: list[str]) -> None:
    title = f"{ISSUE_PREFIX} {year}"
    body = f"""A new ACS vintage appears to be available on Census.

Checked:
- {census_year_url(year)}

Expected files:
- {expected_files(year)[0]}
- {expected_files(year)[1]}

Missing files at check time:
- {", ".join(missing) if missing else "None"}

This issue was opened automatically by the release-check workflow.
"""
    repo.create_issue(title=title, body=body)

def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Missing GITHUB_TOKEN", file=sys.stderr)
        return 1

    year = LATEST_SUPPORTED_YEAR + 1
    ready, missing = census_release_ready(year)

    if not ready:
        print(f"{year} release not ready. Missing: {missing}")
        return 0

    gh = Github(token)
    repo = gh.get_repo(REPO)

    if issue_exists(repo, year):
        print(f"Issue for {year} already exists.")
        return 0

    open_issue(repo, year, missing)
    print(f"Opened issue for {year}.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
