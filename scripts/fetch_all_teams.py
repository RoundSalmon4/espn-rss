#!/usr/bin/env python3
"""Fetch teams for all leagues sequentially."""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent))

from update_feeds import discover_teams, KNOWN_LEAGUE_PATHS, TEAM_CACHE_FILE, TIMEZONE, datetime

def main():
    # Load existing cache
    cache = {}
    if TEAM_CACHE_FILE.exists():
        try:
            cache = json.loads(TEAM_CACHE_FILE.read_text())
            print(f"Loaded existing cache with {len(cache)} leagues")
        except:
            cache = {}
    
    for key, info in KNOWN_LEAGUE_PATHS.items():
        league_path = info["path"]
        
        # Skip if already cached and recent
        entry = cache.get(league_path, {})
        if "teams" in entry and entry["teams"]:
            cache_time = entry.get("time", 0)
            now = datetime.now(TIMEZONE).timestamp()
            if now - cache_time < 86400:  # 24 hours
                print(f"  {key}: Using cached ({len(entry['teams'])} teams)")
                continue
        
        print(f"Fetching {key} ({league_path})...", end=" ", flush=True)
        try:
            teams = discover_teams(league_path)
            print(f"Found {len(teams)} teams")
            cache[league_path] = {"time": datetime.now(TIMEZONE).timestamp(), "teams": teams}
            # Save progress after each league
            TEAM_CACHE_FILE.write_text(json.dumps(cache, indent=2))
        except Exception as e:
            print(f"Error: {e}")
    
    print(f"\nCache saved to {TEAM_CACHE_FILE}")
    total = sum(len(entry.get("teams", {})) for entry in cache.values() if isinstance(entry, dict))
    print(f"Total teams: {total}")

if __name__ == "__main__":
    main()
