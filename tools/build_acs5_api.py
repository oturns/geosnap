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
    parser.add_argument(
        "--no-geometry",
        action="store_true",
        help=(
            "Skip downloading/joining TIGER/Line boundaries. By default the "
            "detailed geometry for the matching vintage is joined so the output "
            "is a GeoDataFrame like the published demographic_profile tables."
        ),
    )
    parser.add_argument("--no-resume", action="store_true", help="Disable resume behavior")
    parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds")
    parser.add_argument("--max-retries", type=int, default=6, help="Maximum request retries")
    parser.add_argument("--backoff", type=float, default=1.0, help="Exponential backoff base")
    parser.add_argument(
        "--api-key",
        default=None,
        help="Census API key. Defaults to the CENSUS env var when omitted.",
    )
    parser.add_argument(
        "--county-level",
        action="store_true",
        help=(
            "Request data one county at a time instead of one state at a time. "
            "This is ~60x more API calls (millions nationally) and is only needed "
            "if state-level requests repeatedly hit Census size limits; by default "
            "the build runs state-level and automatically falls back to county-level "
            "for any state/group that is too large."
        ),
    )
    parser.add_argument(
        "--manifest-interval",
        type=int,
        default=50,
        help=(
            "Max chunk completions between manifest checkpoints. "
            "Lower = more durable, higher = more throughput. Default 50."
        ),
    )
    parser.add_argument(
        "--manifest-period",
        type=float,
        default=5.0,
        help=(
            "Max seconds between manifest checkpoints. Default 5.0."
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    api_key = args.api_key or os.environ.get("CENSUS")

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
                state_level=not args.county_level,
                geometry=not args.no_geometry,
                manifest_interval=args.manifest_interval,
                manifest_period=args.manifest_period,
            )
            print(f"Wrote {out}")


if __name__ == "__main__":
    main()
