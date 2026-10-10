"""Audit ESPN completed-score output for season integrity and duplicates."""
import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

def audit(path):
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("No completed games found")
    ids = [r["game_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate game IDs")
    for row in rows:
        if datetime.fromisoformat(row["kickoff_utc"].replace("Z", "+00:00")).year != 2026:
            raise ValueError("Non-2026 game present")
        if int(row["home_score"]) < 0 or int(row["away_score"]) < 0:
            raise ValueError("Negative score")
        if row["home_team"] == row["away_team"]:
            raise ValueError("Identical opponents")
    return {"games": len(rows), "teams": len(set(
        t for r in rows for t in (r["home_team"], r["away_team"])
    )), "first_game": min(r["kickoff_utc"] for r in rows),
        "last_game": max(r["kickoff_utc"] for r in rows),
        "validation": "passed",
        "limitations": "Final scores only. Offensive points, first-half and overtime not verified."}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="output/completed_2026_scores.csv")
    p.add_argument("--output", default="output/audit.json")
    args = p.parse_args()
    result = audit(Path(args.input))
    Path(args.output).write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
