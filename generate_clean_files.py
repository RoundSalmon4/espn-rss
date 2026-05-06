#!/usr/bin/env python3
"""Generate clean files without smart quotes."""
from pathlib import Path
import os

output_dir = Path("C:/Users/cwekselblatt/Downloads/espn-rss-main/clean_files")
output_dir.mkdir(exist_ok=True)

# Read the correct local file
local_file = Path("C:/Users/cwekselblatt/Downloads/espn-rss-main/scripts/update_feeds.py")
content = local_file.read_text(encoding='utf-8')

# Verify no smart quotes
assert '\u201c' not in content, "Smart double open quote found"
assert '\u201d' not in content, "Smart double close quote found"
assert '\u2018' not in content, "Smart single open quote found"
assert '\u2019' not in content, "Smart single close quote found"

# Write clean copy
(output_dir / "update_feeds.py").write_text(content, encoding='utf-8')
print(f"Written: {output_dir / 'update_feeds.py'}")

# Also copy other files
import shutil
for fname in ["create_team_feeds.py", "fetch_teams.py", "merge_cache.py"]:
    src = Path(f"C:/Users/cwekselblatt/Downloads/espn-rss-main/scripts/{fname}")
    if src.exists():
        shutil.copy(src, output_dir / fname)
        print(f"Copied: {fname}")

print(f"\nAll clean files are in: {output_dir}")
print("Upload these files to your repo.")
