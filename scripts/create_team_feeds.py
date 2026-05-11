#!/usr/bin/env python3
"""Create team feeds from cache."""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent))

from update_feeds import init_team_feed, TEAM_CACHE_FILE, KNOWN_LEAGUE_PATHS, TEAM_DIR

def main():
    cache_file = Path(TEAM_CACHE_FILE)
    if not cache_file.exists():
        print(f"Cache file not found: {cache_file}")
        return
    
    with open(cache_file) as f:
        cache = json.load(f)
    
    # Build a map from league_path to league key (e.g., "basketball/nba" -> "nba")
    path_to_key = {info["path"]: key for key, info in KNOWN_LEAGUE_PATHS.items()}
    
    # Count total teams
    total_teams = 0
    for entry in cache.values():
        if isinstance(entry, dict) and "teams" in entry:
            total_teams += len(entry["teams"])
    
    print(f"Creating feeds for {total_teams} teams...")
    
    created = 0
    for league_path, entry in cache.items():
        if not isinstance(entry, dict) or "teams" not in entry:
            continue
        
        # Convert league_path to league key
        league_key = path_to_key.get(league_path, league_path.split("/")[-1])
        league_name = KNOWN_LEAGUE_PATHS.get(league_key, {}).get("name", league_key.upper())
        teams = entry["teams"]
        
        for abbrev, name in teams.items():
            try:
                # Build the path: rss/teams/{league}/{abbrev}.xml
                path = TEAM_DIR / league_key / f"{abbrev}.xml"
                title = f"{league_name} - {name}"
                link = f"https://www.espn.com/{league_path}/team/_/name/{abbrev}"
                description = f"RSS Feed for {name} ({league_name})"
                init_team_feed(path, title, link, description)
                created += 1
            except Exception as e:
                print(f"  Error creating feed for {name} ({league_key}/{abbrev}): {e}")
    
    print(f"Done! Created {created} feeds.")

if __name__ == "__main__":
    main()
