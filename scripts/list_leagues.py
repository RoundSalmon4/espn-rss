#!/usr/bin/env python3
"""List every league ESPN exposes and flag ones we don't support yet."""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from update_feeds import KNOWN_LEAGUE_PATHS

SPORTS = [
    "australian-football", "baseball", "basketball", "cricket", "field-hockey",
    "football", "golf", "hockey", "lacrosse", "mma", "racing", "rugby",
    "rugby-league", "soccer", "tennis", "volleyball", "water-polo",
]

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "espn-rss/2.0"})
    return json.load(urllib.request.urlopen(req, timeout=25))

def main():
    known = {}
    for key, info in KNOWN_LEAGUE_PATHS.items():
        known[info["path"].split("/")[-1]] = key
    for sport in SPORTS:
        try:
            data = get(f"https://sports.core.api.espn.com/v2/sports/{sport}/leagues?limit=500")
        except Exception as e:
            print(f"[{sport}] error: {e}")
            continue
        slugs = sorted(item["$ref"].split("/")[-1].split("?")[0]
                       for item in data.get("items", []))
        parts = []
        for slug in slugs:
            if slug in known:
                parts.append(f"{slug} (->{known[slug]})")
            else:
                parts.append(f"*{slug}")
        unsupported = [s for s in slugs if s not in known]
        print(f"[{sport}]")
        if parts:
            print("  " + ", ".join(parts))
        if unsupported:
            print(f"  NEW/UNSUPPORTED ({len(unsupported)}): {', '.join(unsupported)}")

if __name__ == "__main__":
    main()