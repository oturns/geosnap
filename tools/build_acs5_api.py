#!/usr/bin/env python

import argparse
import os
from pathlib import Path

from geosnap.io.util import convert_census_acs5


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Build national ACS5 tract/blockgroup demographic profile parquet tables "
            "using the ACS5 detail endpoint only."
        )
    )
    parser.add_argument("--years", nargs="+", required=True, help="Years to build, e.g. 2019 2020")
    parser.add_argument(
        "--levels",
        nargs="+",
        default=["tract", "blockgroup"],
        choices=["tract", "blockgroup", "bg", "tr"],
        help="Geographic levels to build",
    )
    parser.add_argument("--output-dir", default=".", help="Directory for output parquet and cache")
    parser.add_argument("--workers", type=int, default=8, help="Concurrent request workers")
    parser.add_argument("--overwrite", action="store_true", help="Ignore cache/chunks and redownload")
    parser.add_argument("--no-resume", action="store_true", help="Disable resume behavior")
    parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds")
    parser.add_argument("--max-retries", type=int, default=6, help="Maximum request retries")
    parser.add_argument("--backoff", type=float, default=1.0, help="Exponential backoff base")
    parser.add_argument(
        "--api-key",
        default=None,
        help="Census API key. Defaults to CENSUS_API_KEY env var when omitted.",
    )
    parser.add_argument(
        "--state-level",
        action="store_true",
        help=(
            "Request data at the state level instead of county level. "
            "Reduces API calls by ~60x but may hit Census row limits."
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    api_key = args.api_key or os.environ.get("CENSUS_API_KEY")

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    for year in args.years:
        for level in args.levels:
            print(f"Building ACS5 table: year={year} level={level}")
            out = convert_census_acs5(
                year=year,
                level=level,
                output_dir=str(outdir),
                api_key=api_key,
                workers=args.workers,
                overwrite=args.overwrite,
                resume=not args.no_resume,
                timeout=args.timeout,
                max_retries=args.max_retries,
                backoff=args.backoff,
                state_level=args.state_level,
            )
            print(f"Wrote {out}")


if __name__ == "__main__":
    main()
