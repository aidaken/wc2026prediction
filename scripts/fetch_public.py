#!/usr/bin/env python3
"""
Pull WC 2026 results from Wikipedia (free, no API key).

  python scripts/fetch_public.py              # fetch + update bracket + fixtures cache
  python scripts/fetch_public.py --dry-run  # print what would change

Then run predictions:

  python update.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.public_fetch import run_public_fetch
from src.teams import TeamRegistry
from src.utils import DATA_DIR, load_json, setup_logging, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch public WC 2026 data from Wikipedia")
    parser.add_argument("--dry-run", action="store_true", help="Fetch only, don't write files")
    args = parser.parse_args()

    logger = setup_logging()
    teams_doc = load_json(DATA_DIR / "teams.json")
    bracket = load_json(DATA_DIR / "bracket.json")
    teams = teams_doc.get("teams", {})
    registry = TeamRegistry(teams)

    logger.info("Fetching from Wikipedia (groups A–L + knockout rounds)...")
    summary = run_public_fetch(registry, bracket, write_cache=not args.dry_run)

    logger.info(
        "Done: %d group matches, %d knockout matches, %d bracket slots updated",
        summary["group_matches"],
        summary["knockout_matches"],
        summary["bracket_rows_updated"],
    )

    if args.dry_run:
        logger.info("Dry run — no files written")
        return

    write_json(DATA_DIR / "bracket.json", bracket)
    logger.info("Wrote data/bracket.json and data/fixtures_cache.json")
    logger.info("Next: python update.py")


if __name__ == "__main__":
    main()
