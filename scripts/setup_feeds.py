import requests, json
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree

ROOT = Path(__file__).parent.parent
RSS_DIR = ROOT / "rss"
TEAM_DIR = RSS_DIR / "teams"
STATE_FILE = ROOT / "data" / "state.json"
TEAM_CACHE_FILE = ROOT / "data" / "team_cache.json"
BASE_URL = "https://site.api.espn.com/apis/site/v2"
TIMEZONE = __import__('datetime').timezone(__import__('datetime').timedelta(hours=-5))
HEADERS = {"User-Agent": "espn-rss/2.0"}

KNOWN_LEAGUE_PATHS = {
    "nba": {"path": "basketball/nba", "name": "NBA"},
    "wnba": {"path": "basketball/wnba", "name": "WNBA"},
    "mlb": {"path": "baseball/mlb", "name": "MLB"},
    "nhl": {"path": "hockey/nhl", "name": "NHL"},
    "nfl": {"path": "football/nfl", "name": "NFL"},
    "ncaamb": {"path": "basketball/mens-college-basketball", "name": "NCAA Men's Basketball"},
    "ncaawb": {"path": "basketball/womens-college-basketball", "name": "NCAA Women's Basketball"},
    "mls": {"path": "soccer/usa.1", "name": "MLS"},
    "nwsl": {"path": "soccer/usa.nwsl", "name": "NWSL"},
    "premier-league": {"path": "soccer/eng.1", "name": "Premier League"},
    "champions-league": {"path": "soccer/uefa.champions", "name": "UEFA Champions League"},
    "europa-league": {"path": "soccer/uefa.europa", "name": "UEFA Europa League"},
    "ncaaf": {"path": "football/college-football", "name": "NCAA Football"},
    "ncaab": {"path": "baseball/college-baseball", "name": "NCAA Baseball"},
    "ncaasoftball": {"path": "softball/college-softball", "name": "NCAA Softball"},
    "lacrosse": {"path": "lacrosse/ncaa", "name": "NCAA Lacrosse"},
    "wla": {"path": "lacrosse/wnrl", "name": "Women's Lacrosse"},
    "tennis": {"path": "tennis/wta", "name": "WTA Tennis"},
    "atp": {"path": "tennis/atp", "name": "ATP Tennis"},
    "ncaaw": {"path": "volleyball/women-college-volleyball", "name": "NCAA Women's Volleyball"},
    "ncaam": {"path": "volleyball/men-college-volleyball", "name": "NCAA Men's Volleyball"},
    "boxing": {"path": "boxing", "name": "Boxing"},
    "mma": {"path": "mma", "name": "MMA"},
    "f1": {"path": "racing/f1", "name": "Formula 1"},
    "indycar": {"path": "racing/indycar", "name": "IndyCar"},
    "nascar": {"path": "racing/nascar", "name": "NASCAR"},
    "pga": {"path": "golf/pga", "name": "PGA Tour"},
    "lpga": {"path": "golf/lpga", "name": "LPGA Tour"},
    "marching-band": {"path": "marching-band", "name": "College Marching Band"},
}

def discover_teams(league_path):
    """Fetch all teams for a league from ESPN API with pagination"""
    teams = {}
    page = 1
    while True:
        url = f"{BASE_URL}/sports/{league_path}/teams?page={page}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                break
            data = response.json()
            found_teams = False
            for sport in data.get("sports", []):
                for league in sport.get("leagues", []):
                    for team_entry in league.get("teams", []):
                        team = team_entry.get("team", {})
                        abbrev = team.get("abbreviation", "")
                        # Provide custom abbreviations for F1 teams without them
                        if not abbrev and league_path == "racing/f1":
                            name = team.get("displayName", "").lower()
                            if "audi" in name:
                                abbrev = "audi"
                            elif "cadillac" in name:
                                abbrev = "cad"
                        if abbrev:
                            teams[abbrev.lower()] = team.get("displayName", "")
                            found_teams = True
            if not found_teams:
                break
            page += 1
        except Exception as e:
            print(f"Team discovery failed for {league_path}: {e}")
            break
    return teams

def init_team_feed(path, title, link, description):
    """Create an empty RSS feed for a team"""
    if path.exists():
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = title
    SubElement(channel, "link").text = link
    SubElement(channel, "description").text = description
    ElementTree(rss).write(str(path), encoding="utf-8", xml_declaration=True)
    return False

def main():
    import time
    TEAM_DIR.mkdir(parents=True, exist_ok=True)
    RSS_DIR.mkdir(exist_ok=True)
    
    # Load or create cache
    cache = {}
    if TEAM_CACHE_FILE.exists():
        try:
            cache = json.loads(TEAM_CACHE_FILE.read_text())
        except:
            cache = {}
    
    total_teams = 0
    created_feeds = 0
    skipped_feeds = 0
    
    for league, info in KNOWN_LEAGUE_PATHS.items():
        league_path = info["path"]
        print(f"\nProcessing {league} ({info['name']})...")
        
        # Use cache if available
        cache_entry = cache.get(league_path, {})
        if "teams" in cache_entry:
            teams = cache_entry["teams"]
            print(f"  Using cached {len(teams)} teams")
        else:
            print(f"  Fetching teams from ESPN...")
            teams = discover_teams(league_path)
            cache[league_path] = {"time": time.time(), "teams": teams}
            # Save cache after each league (in case of failure)
            TEAM_CACHE_FILE.write_text(json.dumps(cache, indent=2))
            print(f"  Fetched {len(teams)} teams")
        
        total_teams += len(teams)
        
        # Create team feeds
        for abbrev, name in teams.items():
            team_path = TEAM_DIR / f"{league}-{abbrev}.xml"
            if init_team_feed(team_path, f"{league.upper()} – {abbrev} Finals", 
                             "https://espn.com", f"Final games for {name}"):
                skipped_feeds += 1
            else:
                created_feeds += 1
    
    # Create league feeds (empty for now)
    for league, info in KNOWN_LEAGUE_PATHS.items():
        league_path = RSS_DIR / f"{league}.xml"
        if not league_path.exists():
            rss = Element("rss", version="2.0")
            channel = SubElement(rss, "channel")
            SubElement(channel, "title").text = f"espn-rss – {info['name']} Finals"
            SubElement(channel, "link").text = f"https://espn.com/{info['path'].replace('/', '/')}/"
            SubElement(channel, "description").text = f"{info['name']} final scores"
            # Add placeholder item
            item = SubElement(channel, "item")
            SubElement(item, "title").text = "No games available currently"
            SubElement(item, "link").text = f"https://espn.com/{info['path'].replace('/', '/')}/"
            SubElement(item, "guid").text = f"{league}-placeholder"
            SubElement(item, "pubDate").text = "Mon, 01 Jan 2024 00:00:00 +0000"
            ElementTree(rss).write(str(league_path), encoding="utf-8", xml_declaration=True)
    
    # Create all-finals feed
    all_finals = RSS_DIR / "all-finals.xml"
    if not all_finals.exists():
        rss = Element("rss", version="2.0")
        channel = SubElement(rss, "channel")
        SubElement(channel, "title").text = "espn-rss – All Finals"
        SubElement(channel, "link").text = "https://espn.com"
        SubElement(channel, "description").text = "All leagues final scores"
        item = SubElement(channel, "item")
        SubElement(item, "title").text = "No games available currently"
        SubElement(item, "link").text = "https://espn.com"
        SubElement(item, "guid").text = "all-placeholder"
        SubElement(item, "pubDate").text = "Mon, 01 Jan 2024 00:00:00 +0000"
        ElementTree(rss).write(str(all_finals), encoding="utf-8", xml_declaration=True)
    
    print(f"\n{'='*50}")
    print(f"Total teams: {total_teams}")
    print(f"Created feeds: {created_feeds}")
    print(f"Skipped (already existed): {skipped_feeds}")
    print(f"Cache saved to: {TEAM_CACHE_FILE}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()
