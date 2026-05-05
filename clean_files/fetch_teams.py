#!/usr/bin/env python3
"""Fetch teams for specified leagues and update cache."""
from pathlib import Path
import json
import sys
import os

sys.path.insert(0, str(Path(__file__).parent))

ROOT = Path(__file__).parent.parent

from update_feeds import discover_teams, KNOWN_LEAGUE_PATHS, TEAM_CACHE_FILE, TIMEZONE, datetime

def main():
    leagues = sys.argv[1:]  # e.g., "nba", "ncaamb"
    
    if not leagues:
        print("Usage: python fetch_teams.py <league1> <league2> ...")
        sys.exit(1)
    
    # Determine cache file (use suffix from env if present)
    cache_suffix = os.environ.get("CACHE_SUFFIX", "")
    if cache_suffix:
        cache_file = ROOT / "data" / f"team_cache_{cache_suffix}.json"
    else:
        cache_file = TEAM_CACHE_FILE
    
    # Load existing cache
    cache = {}
    if cache_file.exists():
        try:
            cache = json.loads(cache_file.read_text())
        except:
            cache = {}
    
    for league_key in leagues:
        if league_key not in KNOWN_LEAGUE_PATHS:
            print(f"Unknown league: {league_key}")
            continue
        
        # Skip leagues that don't have /teams endpoint
        if not KNOWN_LEAGUE_PATHS[league_key].get("has_teams", True):
            print(f"Skipping {league_key} (no /teams endpoint)")
            continue
        
        league_path = KNOWN_LEAGUE_PATHS[league_key]["path"]
        print(f"Fetching {league_key} ({league_path})...", end=" ", flush=True)
        
        try:
            teams = discover_teams(league_path)
            print(f"Found {len(teams)} teams")
            cache[league_path] = {"time": datetime.now(TIMEZONE).timestamp(), "teams": teams}
        except Exception as e:
            print(f"Error: {e}")
    
    # Save cache
    cache_file.write_text(json.dumps(cache, indent=2))
    print(f"\nCache saved to {cache_file}")
    
    total = sum(len(entry.get("teams", {})) for entry in cache.values() if isinstance(entry, dict))
    print(f"Total teams cached: {total}")

if __name__ == "__main__":
    main()
