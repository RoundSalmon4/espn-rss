#!/usr/bin/env python3
"""Merge separate cache files into one team_cache.json."""
from pathlib import Path
import json
import glob

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

def main():
    merged = {}
    
    # Find all team_cache_*.json files (from artifacts or local)
    # Artifacts download to data/team_cache_NAME/team_cache_NAME.json
    patterns = [
        "team_cache_*.json",
        "team_cache_*/*.json",
        "*/team_cache_*.json"
    ]
    
    cache_files = set()
    for pattern in patterns:
        cache_files.update(glob.glob(str(DATA_DIR / pattern)))
    
    print(f"Found {len(cache_files)} cache files")
    
    for cache_path in cache_files:
        cache_file = Path(cache_path)
        print(f"Merging {cache_file.name}...")
        try:
            data = json.loads(cache_file.read_text())
            # Data is {league_path: {"time": ..., "teams": {...}}}
            for key, value in data.items():
                if isinstance(value, dict) and "teams" in value:
                    merged[key] = value
        except Exception as e:
            print(f"  Error: {e}")
    
    # Write merged cache.
    output = DATA_DIR / "team_cache.json"
    output.write_text(json.dumps(merged, indent=2))
    print(f"\nMerged cache written to {output}")
    
    total = sum(len(entry.get("teams", {})) for entry in merged.values() if isinstance(entry, dict))
    print(f"Total teams: {total}")

if __name__ == "__main__":
    main()
