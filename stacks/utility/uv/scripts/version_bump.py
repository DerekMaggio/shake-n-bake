#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "semver",
# ]
# ///
import semver
import argparse
from pathlib import Path
from typing import Literal


if __name__ == "__main__":
    bump_type_choices = ["major", "minor", "patch"]

    parser = argparse.ArgumentParser(description="Bump version in the version file.")
    parser.add_argument("version", help="Version string", type=str)
    parser.add_argument(
        "bump_type", type=str, choices=bump_type_choices, help="Type of version bump"
    )
    args = parser.parse_args()

    version_info = semver.VersionInfo.parse(args.version)

    match args.bump_type:
        case "major":
            bump_func = version_info.bump_major
        case "minor":
            bump_func = version_info.bump_minor
        case "patch":
            bump_func = version_info.bump_patch
        case _:
            raise ValueError(f"Unknown bump type: {args.bump_type}")

    print(bump_func())
