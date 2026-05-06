#!/usr/bin/env python3
"""Scrape ESPN API calendar data to find tournament dates, then fetch teams from each event."""
import requests
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).parent.parent
TEAM_CACHE_FILE = ROOT / "data" / "team_cache.json"
BASE_URL = "https://site.api.espn.com/apis/site/v2"
HEADERS = {"User-Agent": "espn-rss/2.0"}

# Leagues without /teams endpoint
TARGET_LEAGUES = {
    "ncaasoftball": {"path": "softball/college-softball", "name": "NCAA Softball"},
    "lacrosse": {"path": "lacrosse/ncaa", "name": "NCAA Lacrosse"},
    "wla": {"path": "lacrosse/wnrl", "name": "Women's Lacrosse"},
    "tennis": {"path": "tennis/wta", "name": "WTA Tennis"},
    "atp": {"path": "tennis/atp", "name": "ATP Tennis"},
    "ncaaw": {"path": "volleyball/women-college-volleyball", "name": "NCAA Women's Volleyball"},
    "ncaam": {"path": "volleyball/men-college-volleyball", "name": "NCAA Men's Volleyball"},
    "boxing": {"path": "boxing", "name": "Boxing"},
    "mma": {"path": "mma", "name": "MMA"},
    "indycar": {"path": "racing/indycar", "name": "IndyCar"},
    "nascar": {"path": "racing/nascar", "name": "NASCAR"},
    "pga": {"path": "golf/pga", "name": "PGA Tour"},
    "lpga": {"path": "golf/lpga", "name": "LPGA Tour"},
    "marching-band": {"path": "marching-band", "name": "College Marching Band"},
}

def get_calendar_dates(league_path):
    """Get all tournament dates from the calendar."""
    url = f"{BASE_URL}/sports/{league_path}/scoreboard"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None, r.status_code
        data = r.json()
        leagues_info = data.get("leagues", [])
        if not leagues_info:
            return None, 200
        league_data = leagues_info[0]
        calendar = league_data.get("calendar", [])
        calendar_type = league_data.get("calendarType", "day")
        
        dates = set()
        if calendar_type == "list":
            # Calendar entries are tournaments with start/end dates
            for entry in calendar:
                start = entry.get("startDate", "")
                end = entry.get("endDate", "")
                if start and end:
                    s = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    e = datetime.fromisoformat(end.replace("Z", "+00:00"))
                    current = s
                    while current <= e:
                        dates.add(current.strftime("%Y%m%d"))
                        current += timedelta(days=1)
        elif calendar_type == "day":
            # Calendar entries can be strings (dates) or dicts
            for entry in calendar:
                if isinstance(entry, str):
                    # Just a date string like "2026-05-06"
                    dates.add(entry.replace("-", ""))
                elif isinstance(entry, dict):
                    start = entry.get("startDate", "")
                    if start:
                        s = datetime.fromisoformat(start.replace("Z", "+00:00"))
                        dates.add(s.strftime("%Y%m%d"))
        
        return sorted(dates), 200
    except Exception as e:
        return None, str(e)

def extract_teams_from_date(league_path, date_str):
    """Extract teams/athletes from scoreboard for a specific date."""
    url = f"{BASE_URL}/sports/{league_path}/scoreboard?dates={date_str}"
    teams = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return teams, r.status_code
        data = r.json()
        events = data.get("events", [])
        for event in events:
            # Standard competitions
            for comp in event.get("competitions", []):
                for c in comp.get("competitors", []):
                    if c.get("type") == "team":
                        team = c.get("team", {})
                        abbrev = team.get("abbreviation", "")
                        name = team.get("displayName", "") or team.get("name", "")
                        if abbrev:
                            teams.append((abbrev, name))
                    elif c.get("type") == "athlete":
                        athlete = c.get("athlete", {})
                        display = athlete.get("displayName", "")
                        short = athlete.get("shortName", "")
                        abbrev = short if short else display
                        if display:
                            teams.append((abbrev, display))
            # Tennis-style groupings
            for grouping in event.get("groupings", []):
                for comp in grouping.get("competitions", []):
                    for c in comp.get("competitors", []):
                        if c.get("type") == "athlete":
                            athlete = c.get("athlete", {})
                            display = athlete.get("displayName", "")
                            short = athlete.get("shortName", "")
                            abbrev = short if short else display
                            if display:
                                teams.append((abbrev, display))
        return teams, 200
    except Exception:
        return teams, 0

def cache_team(league_path, abbrev, name, cache):
    if league_path not in cache:
        cache[league_path] = {"time": 0, "teams": {}}
    teams = cache[league_path].get("teams", {})
    if not isinstance(teams, dict):
        teams = {}
    key = abbrev.lower()
    if key not in teams and key:
        teams[key] = name
        cache[league_path]["teams"] = teams
        return True
    return False

def main():
    # Load existing cache
    cache = {}
    if TEAM_CACHE_FILE.exists():
        try:
            cache = json.loads(TEAM_CACHE_FILE.read_text())
        except:
            cache = {}
    
    total_new = 0
    call_count = 0
    skipped = []
    
    for league_key, league_info in TARGET_LEAGUES.items():
        path = league_info["path"]
        print(f"\n=== {league_key} ({league_info['name']}) ===")
        
        # Get calendar dates
        calendar_dates, status = get_calendar_dates(path)
        if calendar_dates is None:
            print(f"  No calendar data (status: {status}), skipping")
            skipped.append(f"{league_key}: ESPN API returned {status}")
            continue
        
        print(f"  Calendar has {len(calendar_dates)} dates to check")
        
        league_new = 0
        success_count = 0
        error_count = 0
        
        for date_str in calendar_dates:
            teams, status = extract_teams_from_date(path, date_str)
            call_count += 1
            
            if status == 200 and teams:
                success_count += 1
                for abbrev, name in teams:
                    if cache_team(path, abbrev, name, cache):
                        league_new += 1
                        total_new += 1
            elif status != 200:
                error_count += 1
            
            # Rate limit
            if call_count % 100 == 0:
                time.sleep(1)
        
        team_count = len(cache.get(path, {}).get("teams", {}))
        print(f"  Results: {team_count} teams total, {league_new} new from this run")
        print(f"  API: {success_count} dates with data, {error_count} errors out of {len(calendar_dates)} calls")
    
    # Save cache
    (ROOT / "data").mkdir(parents=True, exist_ok=True)
    TEAM_CACHE_FILE.write_text(json.dumps(cache, indent=2))
    print(f"\n=== FINAL SUMMARY ===")
    print(f"Total API calls: {call_count}")
    print(f"Total new teams: {total_new}")
    print(f"Skipped: {len(skipped)}")
    for s in skipped:
        print(f"  {s}")
    print(f"Cache: {TEAM_CACHE_FILE}")
    
    for path, entry in sorted(cache.items()):
        if isinstance(entry, dict) and "teams" in entry:
            team_count = len(entry["teams"])
            if team_count > 0:
                print(f"  {path}: {team_count} teams")

if __name__ == "__main__":
    main()
