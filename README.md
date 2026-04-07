# ESPN RSS Feeds

Auto-generated RSS feeds for sports scores using the ESPN API.

## Features

- **Auto-discovery** - Automatically finds all sports available from ESPN
- **Real-time updates** - Games appear within minutes of going final
- **Team-specific feeds** - Separate feeds for each team
- **No duplicates** - Uses team IDs to prevent duplicate entries

## Feeds Generated

### League feeds
- `/rss/<league>.xml` (e.g., `/rss/nba.xml`, `/rss/mlb.xml`)

### Team feeds
- `/rss/teams/<league>-<team>.xml`

### Combined feed
- `/rss/all-finals.xml`

## Supported Sports

29 sports/leagues including:
- NBA, WNBA, MLB, NHL, NFL
- NCAA Men's/Women's Basketball
- NCAA Baseball, NCAA Softball
- NCAA Football
- NCAA Lacrosse
- MLS, NWSL
- Premier League
- UEFA Champions League
- UEFA Europa League

Plus: Tennis, ATP, Boxing, MMA, F1, IndyCar, NASCAR, PGA, LPGA

## Behavior

- Only shows today's and yesterday's games
- One item per game (uses ESPN team IDs for uniqueness)
- Published when game goes FINAL
- OT games marked with `(OT)`
- Updated automatically by GitHub Actions every 30 minutes

## Technical Notes

- Uses ESPN's undocumented JSON API (`site.api.espn.com`)
- Runs on GitHub Actions (Ubuntu)
- State persisted in `data/state.json` to prevent duplicates
- Parallel fetching with ThreadPoolExecutor
