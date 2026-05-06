#!/usr/bin/env python3
"""Test which leagues have working /teams endpoints."""
import requests

BASE_URL = "https://site.api.espn.com/apis/site/v2"

paths = [
    "softball/college-softball",
    "volleyball/women-college-volleyball",
    "volleyball/men-college-volleyball",
    "lacrosse/ncaa",
    "lacrosse/wnrl",
    "tennis/wta",
    "tennis/atp",
    "golf/pga",
    "golf/lpga",
    "racing/indycar",
    "racing/nascar",
    "boxing",
    "mma",
    "marching-band",
]

for path in paths:
    url = f"{BASE_URL}/sports/{path}/teams"
    try:
        r = requests.get(url, timeout=5)
        print(f"{path}: {r.status_code}")
    except Exception as e:
        print(f"{path}: ERROR - {e}")
