#!/usr/bin/env python3
"""Build team cache incrementally, saving progress after each league."""
from pathlib import Path
import json
import sys
import signal

sys.path.insert(0, str(Path(__file__).parent))

from update_feeds import discover_teams, KNOWN_LEAGUE_PATHS, TEAM_CACHE_FILE, TIMEZONE, datetime

def timeout_handler(signum, frame):
    raise TimeoutError("League fetch timed out")

def main():
    # Load existing cache if any
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
            # Set 3-minute timeout per league
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(180)
            
            teams = discover_teams(league_path)
            signal.alarm(0)
            print(f"Found {len(teams)} teams")
            
            # Save progress after each league
            cache[league_path] = {"time": datetime.now(TIMEZONE).timestamp(), "teams": teams}
            TEAM_CACHE_FILE.write_text(json.dumps(cache, indent=2))
        except TimeoutError:
            signal.alarm(0)
            print(f"TIMED OUT - skipping")
        except Exception as e:
            signal.alarm(0)
            print(f"Error: {e}")
    
    print(f"\nCache saved to {TEAM_CACHE_FILE}")
    total = sum(len(entry.get("teams", {})) for entry in cache.values() if isinstance(entry, dict))
    print(f"Total teams: {total}")
    print(f"Leagues cached: {len([e for e in cache.values() if isinstance(e, dict) and e.get('teams')])}")

if __name__ == "__main__":
    main()
