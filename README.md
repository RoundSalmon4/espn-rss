# ESPN RSS Feeds

Auto-generated RSS feeds for sports scores using the ESPN API.

## Features

- **Real-time updates** - Games appear within minutes of going final
- **Team-specific feeds** - Separate feeds for each team
- **No duplicates** - Uses team IDs to prevent duplicate entries
- **All 29 leagues supported** - From major pro sports to college and international

## Feeds Available

### League Feeds
- `/rss/<league>.xml` (e.g., `/rss/nba.xml`, `/rss/mlb.xml`)

### Team Feeds

Team feeds are available in two URL formats - both work:

**Subdirectory format (preferred):**
- `/rss/teams/<league>/<team>.xml` (e.g., `/rss/teams/nba/lal.xml`)

**Hyphen format (legacy, still supported):**
- `/rss/teams/<league>-<team>.xml` (e.g., `/rss/teams/nba-lal.xml`)

- **Pre-created:** Most leagues have all team feeds ready immediately (empty feeds won't trigger notifications)
- **On-demand:** Some leagues create team feeds as games are played - more teams appear over time

### Combined Feed
- `/rss/all-finals.xml` - All leagues in one feed

## Supported Leagues (29 total)

**Major Pro Sports:**
- NBA, WNBA, MLB, NHL, NFL

**College Sports:**
- NCAA Men's Basketball, NCAA Women's Basketball
- NCAA Football, NCAA Baseball, NCAA Softball
- NCAA Lacrosse, Women's Lacrosse
- NCAA Men's Volleyball, NCAA Women's Volleyball

**Soccer:**
- MLS, NWSL
- Premier League, UEFA Champions League, UEFA Europa League

**Individual & Racing:**
- Tennis (WTA), ATP Tennis
- Boxing, MMA
- Formula 1, IndyCar, NASCAR
- PGA Tour, LPGA Tour

**Other:**
- College Marching Band

## How Team Feeds Work

### Leagues with pre-created team feeds:
NBA, WNBA, MLB, NHL, NFL, NCAA Basketball (M+W), NCAA Football, NCAA Baseball, MLS, NWSL, Premier League, Champions League, Europa League, Formula 1.

These leagues have all team feeds created immediately - subscribe to any team right away. Empty feeds have no `pubDate` so they won't trigger notifications until a game is posted. Team feeds exist in both subdirectory (`/rss/teams/nba/lal.xml`) and hyphen (`/rss/teams/nba-lal.xml`) formats.

### Leagues with on-demand team feeds:
NCAA Softball, Lacrosse, Women's Lacrosse, Tennis, ATP, NCAA Volleyball (M+W), Boxing, MMA, IndyCar, NASCAR, PGA, LPGA, Marching Band.

These leagues don't have a team directory API. Team feeds are created automatically when a game is played - subscribe to the feed URL and it will appear after that team's first game. Over time, all active teams will have feeds. Feeds use the subdirectory format (`/rss/teams/<league>/<team>.xml`).

## Feed Behavior

- **Shows recent games** - Today's and yesterday's completed games
- **One item per game** - Uses ESPN team IDs for uniqueness
- **OT marker** - Overtime games marked with `(OT)`
- **Updated automatically** - GitHub Actions runs every 30 minutes
- **Empty feeds are safe** - No `pubDate` until games exist, so no spurious notifications.

## Example Feed URLs

### League Feeds
- All NBA games: `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/nba.xml`
- All NFL games: `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/nfl.xml`
- All finals: `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/all-finals.xml`

### Team Feeds (Subdirectory Format)
- Lakers (NBA): `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/teams/nba/lal.xml`
- Chiefs (NFL): `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/teams/nfl/kc.xml`
- Dodgers (MLB): `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/teams/mlb/lad.xml`
- Oilers (NHL): `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/teams/nhl/edm.xml`
- Aces (WNBA): `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/teams/wnba/lv.xml`
- Ohio State (NCAA MBK): `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/teams/ncaamb/osu.xml`
- Oregon State (NCAA Baseball): `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/teams/ncaab/orst.xml`
- Oregon State (NCAA Football): `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/teams/ncaaf/orst.xml`
- Liverpool (Premier League): `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/teams/premier-league/liv.xml`

### Team Feeds (Hyphen Format - Legacy)
- Lakers (NBA): `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/teams/nba-lal.xml`
- Chiefs (NFL): `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/teams/nfl-kc.xml`
- Dodgers (MLB): `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/teams/mlb-lad.xml`
- Oilers (NHL): `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/teams/nhl-edm.xml`
- Aces (WNBA): `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/teams/wnba-lv.xml`
- Liverpool (Premier League): `https://raw.githubusercontent.com/RoundSalmon4/espn-rss/main/rss/teams/premier-league-liv.xml`
