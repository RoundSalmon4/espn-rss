#!/usr/bin/env python3
"""Create team cache by discovering all teams."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from update_feeds import discover_teams, KNOWN_LEAGUE_PATHS, TEAM_CACHE_FILE

def main():
    print("Discovering teams for all sports...")
    for key, info in KNOWN_LEAGUE_PATHS.items():
        league_path = info["path"]
        print(f"Processing {key} ({league_path})...")
        try:
            teams = discover_teams(league_path)
            print(f"  Found {len(teams)} teams")
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"Team cache saved to {TEAM_CACHE_FILE}")

if __name__ == "__main__":
    main()
