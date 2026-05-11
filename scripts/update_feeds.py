import requests, json, re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from xml.etree.ElementTree import Element, SubElement, ElementTree
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).parent.parent
STATE_FILE = ROOT / "data" / "state.json"
RSS_DIR = ROOT / "rss"
TEAM_DIR = RSS_DIR / "teams"
TEAM_CACHE_FILE = ROOT / "data" / "team_cache.json"
TEAM_CACHE_TTL = 86400  # 24 hours in seconds

BASE_URL = "https://site.api.espn.com/apis/site/v2"
TIMEZONE = timezone(timedelta(hours=-5))
HEADERS = {"User-Agent": "espn-rss/2.0"}

KNOWN_LEAGUE_PATHS = {
    "nba": {"path": "basketball/nba", "name": "NBA", "has_teams": True},
    "wnba": {"path": "basketball/wnba", "name": "WNBA", "has_teams": True},
    "mlb": {"path": "baseball/mlb", "name": "MLB", "has_teams": True},
    "nhl": {"path": "hockey/nhl", "name": "NHL", "has_teams": True},
    "nfl": {"path": "football/nfl", "name": "NFL", "has_teams": True},
    "ncaamb": {"path": "basketball/mens-college-basketball", "name": "NCAA Men's Basketball", "has_teams": True},
    "ncaawb": {"path": "basketball/womens-college-basketball", "name": "NCAA Women's Basketball", "has_teams": True},
    "mls": {"path": "soccer/usa.1", "name": "MLS", "has_teams": True},
    "nwsl": {"path": "soccer/usa.nwsl", "name": "NWSL", "has_teams": True},
    "premier-league": {"path": "soccer/eng.1", "name": "Premier League", "has_teams": True},
    "champions-league": {"path": "soccer/uefa.champions", "name": "UEFA Champions League", "has_teams": True},
    "europa-league": {"path": "soccer/uefa.europa", "name": "UEFA Europa League", "has_teams": True},
    "ncaaf": {"path": "football/college-football", "name": "NCAA Football", "has_teams": True},
    "ncaab": {"path": "baseball/college-baseball", "name": "NCAA Baseball", "has_teams": True},
    "ncaasoftball": {"path": "softball/college-softball", "name": "NCAA Softball", "has_teams": False},
    "lacrosse": {"path": "lacrosse/ncaa", "name": "NCAA Lacrosse", "has_teams": False},
    "wla": {"path": "lacrosse/wnrl", "name": "Women's Lacrosse", "has_teams": False},
    "tennis": {"path": "tennis/wta", "name": "WTA Tennis", "has_teams": False},
    "atp": {"path": "tennis/atp", "name": "ATP Tennis", "has_teams": False},
    "ncaaw": {"path": "volleyball/women-college-volleyball", "name": "NCAA Women's Volleyball", "has_teams": False},
    "ncaam": {"path": "volleyball/men-college-volleyball", "name": "NCAA Men's Volleyball", "has_teams": False},
    "boxing": {"path": "boxing", "name": "Boxing", "has_teams": False},
    "mma": {"path": "mma", "name": "MMA", "has_teams": False},
    "f1": {"path": "racing/f1", "name": "Formula 1", "has_teams": True},
    "indycar": {"path": "racing/indycar", "name": "IndyCar", "has_teams": False},
    "nascar": {"path": "racing/nascar", "name": "NASCAR", "has_teams": False},
    "pga": {"path": "golf/pga", "name": "PGA Tour", "has_teams": False},
    "lpga": {"path": "golf/lpga", "name": "LPGA Tour", "has_teams": False},
    "marching-band": {"path": "marching-band", "name": "College Marching Band", "has_teams": False},
}

SPORTS = [info["path"] for info in KNOWN_LEAGUE_PATHS.values()]

def discover_leagues():
    discovered = {}
    url = f"{BASE_URL}/sports"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            data = response.json()
            for sport in data.get("sports", []):
                for league_info in sport.get("leagues", []):
                    league_slug = league_info.get("slug", "")
                    league_name = league_info.get("name", "")
                    if league_slug:
                        key = league_slug.replace("-", "_").replace(" ", "_").lower()[:20]
                        if key and league_name:
                            path = f"{sport.get('slug', '')}/{league_slug}"
                            discovered[key] = {"path": path, "name": league_name}
    except Exception as e:
        print(f"Auto-discovery failed: {e}")
    for key, info in KNOWN_LEAGUE_PATHS.items():
        if key not in discovered:
            discovered[key] = info
    return discovered

def discover_teams(league_path):
    cache = {}
    if TEAM_CACHE_FILE.exists():
        try:
            cache = json.loads(TEAM_CACHE_FILE.read_text())
        except:
            cache = {}
    cache_entry = cache.get(league_path, {})
    cache_time = cache_entry.get("time", 0)
    now = datetime.now(TIMEZONE).timestamp()
    if now - cache_time < TEAM_CACHE_TTL and "teams" in cache_entry:
        print(f"Using cached teams for {league_path}")
        return cache_entry["teams"]
    teams = {}
    page = 1
    max_pages = 30
    while page <= max_pages:
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
    if teams:
        cache[league_path] = {"time": now, "teams": teams}
        TEAM_CACHE_FILE.write_text(json.dumps(cache, indent=2))
    else:
        # API failed; keep existing cached data if available
        if cache_entry.get("teams"):
            print(f"  API returned no teams for {league_path}, keeping {len(cache_entry['teams'])} cached teams")
            return cache_entry["teams"]
    return teams

def validate_state(state):
    if "published" not in state:
        state["published"] = {}
    now = datetime.now(TIMEZONE)
    today = now.strftime("%Y-%m-%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    valid_dates = {today, yesterday}
    for league, games in list(state.get("published", {}).items()):
        if not isinstance(games, dict):
            state["published"][league] = {}
            continue
        keys_to_remove = set()
        for gid, title in games.items():
            match = re.match(r"([a-z\-]+)-(\d+)-(\d+)-(\d{4}-\d{2}-\d{2})", gid)
            if not match:
                keys_to_remove.add(gid)
                continue
            league_key, team1, team2, date = match.groups()
            if date not in valid_dates:
                keys_to_remove.add(gid)
                continue
        for key in keys_to_remove:
            del games[key]
    return state

def load_state():
    if not STATE_FILE.exists():
        return {"published": {}}
    data = json.loads(STATE_FILE.read_text())
    now = datetime.now(TIMEZONE)
    today = now.strftime("%Y-%m-%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    valid_dates = {today, yesterday}
    for league, items in data.get("published", {}).items():
        if isinstance(items, list):
            new_dict = {}
            for item in items:
                new_dict[item] = ""
            data["published"][league] = new_dict
    for league, games in list(data.get("published", {}).items()):
        keys_to_remove = set()
        for gid in games.keys():
            match = re.match(r"([a-z\-]+)-(\d+)-(\d+)-(\d{4}-\d{2}-\d{2})", gid)
            if match and match.group(4) not in valid_dates:
                keys_to_remove.add(gid)
        for gid in keys_to_remove:
            del games[gid]
    return data

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def fetch_espn(league_info, date_str):
    path = league_info["path"]
    url = f"{BASE_URL}/sports/{path}/scoreboard?dates={date_str.replace('-', '')}"
    groups_sports = ["basketball/mens-college-basketball", "basketball/womens-college-basketball", 
                     "football/college-football", "volleyball", "softball"]
    if any(sport in path for sport in groups_sports):
        url += "&groups=50"
    print(f"Fetching: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error: {e}")
    return {"events": []}

def extract_games_espn(data, league):
    games = []
    for event in data.get("events", []):
        competition = event.get("competitions", [{}])[0]
        if not competition:
            continue
        status = competition.get("status", {}).get("type", {})
        if status.get("completed") != True:
            continue
        competitors = competition.get("competitors", [])
        if len(competitors) != 2:
            continue
        away = competitors[0]
        home = competitors[1]
        if away.get("homeAway") == "home":
            away, home = home, away
        away_score = away.get("score", "0")
        home_score = home.get("score", "0")
        if not away_score or not home_score:
            continue
        away_team = away.get("team", {})
        home_team = home.get("team", {})
        away_abbrev = away_team.get("abbreviation", "")
        home_abbrev = home_team.get("abbreviation", "")
        if not away_abbrev or not home_abbrev:
            continue
        away_id = away_team.get("id", "")
        home_id = home_team.get("id", "")
        period = competition.get("status", {}).get("period", 0)
        is_ot = period > 4 and status.get("type") == "STATUS_FINAL"
        ot_suffix = " (OT)" if is_ot else ""
        title = f"{away_abbrev} {away_score} - {home_abbrev} {home_score} (Final){ot_suffix}"
        games.append({
            "away_code": away_abbrev,
            "away_name": away_team.get("name", ""),
            "away_score": away_score,
            "away_id": away_id,
            "home_code": home_abbrev,
            "home_name": home_team.get("name", ""),
            "home_score": home_score,
            "home_id": home_id,
            "ot": ot_suffix,
            "title": title
        })
    print(f"Extracted {len(games)} games for {league}")
    return games

def load_existing_items(path):
    if not path.exists():
        return []
    root = ElementTree(file=path).getroot()
    channel = root.find("channel")
    if channel is None:
        return []
    items = []
    for item in channel.findall("item"):
        guid = item.find("guid")
        if guid is not None and guid.text and "placeholder" not in guid.text:
            items.append(item)
    return items

def write_feed(path, title, link, description, new_items, state=None):
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = title
    SubElement(channel, "link").text = link
    SubElement(channel, "description").text = description
    existing_guids = set()
    for item in load_existing_items(path):
        guid = item.find("guid")
        if guid is not None and guid.text:
            existing_guids.add(guid.text)
            channel.append(item)
    for gid, txt in new_items:
        if gid in existing_guids:
            continue
        existing_guids.add(gid)
        it = SubElement(channel, "item")
        SubElement(it, "title").text = txt
        SubElement(it, "link").text = link
        SubElement(it, "guid").text = gid
        SubElement(it, "pubDate").text = datetime.now(TIMEZONE).strftime("%a, %d %b %Y %H:%M:%S %z")
    ElementTree(rss).write(str(path), encoding="utf-8", xml_declaration=True)

def cache_team(league_path, abbrev, name):
    try:
        cache = {}
        if TEAM_CACHE_FILE.exists():
            try:
                text = TEAM_CACHE_FILE.read_text()
                cache = json.loads(text)
            except:
                cache = {}
        if league_path not in cache:
            cache[league_path] = {"time": 0, "teams": {}}
        teams = cache[league_path].get("teams", {})
        if not isinstance(teams, dict):
            teams = {}
        key = abbrev.lower()
        if key not in teams:
            teams[key] = name
            cache[league_path]["teams"] = teams
            TEAM_CACHE_FILE.write_text(json.dumps(cache, indent=2))
    except Exception as e:
        print("Error caching team: " + str(e))

def init_team_feed(path, title, link, description):
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = title
    SubElement(channel, "link").text = link
    SubElement(channel, "description").text = description
    ElementTree(rss).write(str(path), encoding="utf-8", xml_declaration=True)

def write_feed_from_state(path, title, link, description, league, state, leagues=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = title
    SubElement(channel, "link").text = link
    SubElement(channel, "description").text = description
    now = datetime.now(TIMEZONE)
    today = now.strftime("%Y-%m-%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    valid_dates = {today, yesterday}
    published = {}
    if league == "all":
        for league_key, league_games in state.get("published", {}).items():
            for gid, title_text in league_games.items():
                match = re.match(r"([a-z\-]+)-(\d+)-(\d+)-(\d{4}-\d{2}-\d{2})", gid)
                if match and match.group(4) in valid_dates:
                    published[gid] = f"{league_key.upper()}: {title_text}"
    else:
        league_games = state.get("published", {}).get(league, {})
        for gid, title_text in league_games.items():
            match = re.match(r"([a-z\-]+)-(\d+)-(\d+)-(\d{4}-\d{2}-\d{2})", gid)
            if match and match.group(4) in valid_dates:
                published[gid] = title_text
    existing_guids = set()
    if path.exists():
        for item in load_existing_items(path):
            guid = item.find("guid")
            if guid is not None and guid.text:
                existing_guids.add(guid.text)
                channel.append(item)
    for gid, title_text in published.items():
        if gid in existing_guids:
            continue
        if league == "all":
            title_with_league = title_text
        else:
            match = re.match(r"([a-z]+)-(\d+)-(\d+)-(\d{4}-\d{2}-\d{2})", gid)
            if match:
                league_key = match.group(1)
                title_with_league = f"{league_key.upper()}: {title_text}"
            else:
                title_with_league = gid
        existing_guids.add(gid)
        it = SubElement(channel, "item")
        SubElement(it, "title").text = str(title_with_league)
        SubElement(it, "link").text = link
        SubElement(it, "guid").text = gid
        SubElement(it, "pubDate").text = datetime.now(TIMEZONE).strftime("%a, %d %b %Y %H:%M:%S %z")
    if not published:
        it = SubElement(channel, "item")
        SubElement(it, "title").text = "No games available currently"
        SubElement(it, "link").text = link
        SubElement(it, "guid").text = f"{league}-placeholder"
        SubElement(it, "pubDate").text = datetime.now(TIMEZONE).strftime("%a, %d %b %Y %H:%M:%S %z")
    ElementTree(rss).write(str(path), encoding="utf-8", xml_declaration=True)

def main():
    state = load_state()
    state.setdefault("published", {})
    all_new = []
    now = datetime.now(TIMEZONE)
    today = now.strftime("%Y-%m-%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"Today: {today}, Yesterday: {yesterday}")
    leagues = discover_leagues()
    print(f"Leagues: {list(leagues.keys())}")
    for league, league_info in leagues.items():
        if league_info.get("has_teams", True):
            teams = discover_teams(league_info["path"])
            print(f"Discovered {len(teams)} teams for {league}")
            for team_abbrev, team_name in teams.items():
                team_path = TEAM_DIR / league / f"{team_abbrev}.xml"
                if not team_path.exists():
                    title = f"{league_info['name']} - {team_name}"
                    link = f"https://www.espn.com/{league_info['path']}/team/_/name/{team_abbrev}"
                    description = f"RSS Feed for {team_name} ({league_info['name']})"
                    init_team_feed(team_path, title, link, description)
        else:
            print(f"Skipping team discovery for {league} (no /teams endpoint)")
    def fetch_date_combo(args):
        league, league_info, date_str = args
        data = fetch_espn(league_info, date_str)
        return league, date_str, data
    fetch_tasks = []
    for league, league_info in leagues.items():
        for date_str in [today, yesterday]:
            fetch_tasks.append((league, league_info, date_str))
    games_cache = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_date_combo, task) for task in fetch_tasks]
        for future in as_completed(futures):
            try:
                league, date_str, data = future.result()
                games = extract_games_espn(data, league)
                games_cache[(league, date_str)] = games
            except Exception as e:
                print(f"Error: {e}")
    seen_base_gids_this_run = set()
    print(f"=== Processing {len(leagues)} leagues: {list(leagues.keys())} ===")
    for league, league_info in leagues.items():
        print(f"Processing league: {league}")
        state["published"].setdefault(league, {})
        league_new = []
        for date_str in [today, yesterday]:
            games = games_cache.get((league, date_str), [])
            game_ids_seen = {}
            for game in games:
                away_code = game["away_code"]
                home_code = game["home_code"]
                away_id = game.get("away_id", "")
                home_id = game.get("home_id", "")
                if away_id and home_id:
                    team_ids = sorted([away_id, home_id])
                    unique_key = f"{league}-{team_ids[0]}-{team_ids[1]}"
                else:
                    if away_code > home_code:
                        away_code, home_code = home_code, away_code
                    unique_key = f"{league}-{away_code}-{home_code}"
                if unique_key in seen_base_gids_this_run:
                    continue
                already_published = False
                for existing_gid, existing_title in state["published"].get(league, {}).items():
                    if existing_title == game["title"]:
                        already_published = True
                        break
                seen_base_gids_this_run.add(unique_key)
                gid = f"{unique_key}-{date_str}"
                title = game["title"]
                state["published"][league][gid] = title
                print(f"SAVED: {league} -> {gid}")
                for team_code, team_name in [(game["away_code"], game["away_name"]), (game["home_code"], game["home_name"])]:
                    league_path = leagues[league]["path"]
                    cache_team(league_path, team_code, team_name)
                    team_path = TEAM_DIR / league / f"{team_code.lower()}.xml"
                    if not team_path.exists():
                        title_text = f"{league_info['name']} - {team_name}"
                        link = f"https://www.espn.com/{league_path}/team/_/name/{team_code}"
                        description = f"RSS Feed for {team_name} ({league_info['name']})"
                        init_team_feed(team_path, title_text, link, description)
                    write_feed(team_path, f"{league_info['name']} - {team_code} Finals", "https://espn.com", f"Final games for {team_code}", [(gid, title)], state)
                if already_published:
                    continue
                league_new.append((gid, title))
                all_new.append((gid, f"{league.upper()}: {title}"))
        url = f"https://espn.com/{league_info['path'].replace('/', '/')}/"
        if league_new:
            write_feed(
                RSS_DIR / f"{league}.xml",
                f"{league_info['name']} - Finals",
                url,
                f"{league_info['name']} final scores",
                league_new,
                state
            )
        else:
            write_feed_from_state(
                RSS_DIR / f"{league}.xml",
                f"{league_info['name']} - Finals",
                url,
                f"{league_info['name']} final scores",
                league,
                state,
                leagues
            )
    save_state(state)
    write_feed_from_state(
        RSS_DIR / "all-finals.xml",
        "All Leagues - Finals",
        "https://espn.com",
        "All leagues final scores",
        "all",
        state,
        leagues
    )
    state = validate_state(state)
    save_state(state)

if __name__ == "__main__":
    main()
