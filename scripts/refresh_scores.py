"""Refresh completed 2026 college-football scores. No betting predictions."""
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
import requests

URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"

def normalize(event):
    if not event.get("status", {}).get("type", {}).get("completed", False):
        return None
    comps = event.get("competitions") or []
    if not comps:
        return None
    competitors = comps[0].get("competitors") or []
    if len(competitors) != 2:
        return None
    sides = {x.get("homeAway"): x for x in competitors}
    if set(sides) != {"home", "away"}:
        return None
    try:
        kickoff = event["date"]
        if datetime.fromisoformat(kickoff.replace("Z", "+00:00")).year != 2026:
            return None
        return {"game_id": str(event["id"]), "kickoff_utc": kickoff,
                "home_team": sides["home"]["team"]["displayName"],
                "away_team": sides["away"]["team"]["displayName"],
                "home_score": int(sides["home"]["score"]),
                "away_score": int(sides["away"]["score"])}
    except (KeyError, TypeError, ValueError):
        return None

def refresh(out, weeks=range(0, 17)):
    out.mkdir(parents=True, exist_ok=True)
    rows = {}
    for week in weeks:
        response = requests.get(URL, params={"dates": "2026", "week": week, "groups": 80, "limit": 500}, timeout=35)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data.get("events"), list):
            raise ValueError(f"Missing ESPN events for week {week}")
        for event in data["events"]:
            game = normalize(event)
            if game:
                rows[game["game_id"]] = game
    if not rows:
        raise RuntimeError("No completed 2026 games; refusing empty output")
    path = out / "completed_2026_scores.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(next(iter(rows.values())).keys()))
        writer.writeheader()
        writer.writerows(sorted(rows.values(), key=lambda x: (x["kickoff_utc"], x["game_id"])))
    (out / "manifest.json").write_text(json.dumps({
        "season": 2026, "completed_games": len(rows),
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "source": URL,
        "warning": "Team points are not verified offensive points; completion times are not known."
    }, indent=2))
    print(f"Wrote {len(rows)} completed games to {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()
    refresh(Path(parser.parse_args().output_dir))
