#!/usr/bin/env python3
"""
Script to load the showcase-ecommerce sample datapack into DataHub.
Uses the official DataHub CLI command:
`datahub datapack load showcase-ecommerce --force`
"""
import sys
import subprocess


def load_showcase_ecommerce():
    print("Loading showcase-ecommerce datapack into DataHub...")
    load_cmd = ["datahub", "datapack", "load", "showcase-ecommerce", "--force"]
    result = subprocess.run(load_cmd, capture_output=True, text=True)
    print("DATAPACK LOAD STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("DATAPACK LOAD STDERR:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"Failed to load showcase-ecommerce datapack (exit code {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)
    
    print("\nSuccessfully loaded showcase-ecommerce datapack!")


if __name__ == "__main__":
    load_showcase_ecommerce()
