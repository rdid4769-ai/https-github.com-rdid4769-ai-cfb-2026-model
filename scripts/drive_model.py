"""2026-only offensive drive scoring and matchup projections.

Input drive CSV fields:
game_id,game_date,team,opponent,drive_id,offensive_points
Optional: half, overtime, opponent_points (not used).
offensive_points MUST exclude defensive/special-teams scores and PATs
not credited to this offensive possession. No fabricated drive parsing.
"""
import csv
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

REQUIRED = {"game_id","game_date","team","opponent","drive_id","offensive_points"}

def load_drives(path, as_of):
    cutoff = date.fromisoformat(as_of)
    with Path(path).open(newline="") as f:
        reader = csv.DictReader(f)
        if not REQUIRED.issubset(reader.fieldnames or []):
            raise ValueError("Missing required drive columns")
        rows = list(reader)
    seen = set()
    valid = []
    for row in rows:
        d = date.fromisoformat(row["game_date"][:10])
        if d.year != 2026:
            raise ValueError("Non-2026 data is forbidden")
        if d >= cutoff:
            continue  # no look-ahead
        if row.get("overtime", "").lower() in ("1", "true", "yes"):
            continue
        key = (row["game_id"],row["team"],row["drive_id"])
        if key in seen:
            raise ValueError("Duplicate offensive drive")
        seen.add(key)
        pts = float(row["offensive_points"])
        if pts < 0 or pts > 8:
            raise ValueError("Offensive points per drive out of range")
        valid.append({**row, "offensive_points":pts})
    return valid

def ratings(rows, min_drives=10, prior_strength=20):
    """Shrink team scoring and defensive points allowed per drive to 2026 league mean."""
    if not rows:
        return {}
    league = sum(r["offensive_points"] for r in rows) / len(rows)
    offense, defense = defaultdict(list), defaultdict(list)
    for r in rows:
        offense[r["team"]].append(r["offensive_points"])
        defense[r["opponent"]].append(r["offensive_points"])
    result = {}
    for team in set(offense) | set(defense):
        op, de = offense[team], defense[team]
        if len(op) < min_drives or len(de) < min_drives:
            continue
        result[team] = {
            "off_ppd": (sum(op)+prior_strength*league)/(len(op)+prior_strength),
            "def_ppd_allowed": (sum(de)+prior_strength*league)/(len(de)+prior_strength),
            "off_drives":len(op), "def_drives":len(de)}
    return result

def project(home, away, ratings_by_team, expected_drives=11, home_edge_points=2.0):
    """Baseline projection; not calibrated to odds or opponent strength."""
    h, a = ratings_by_team[home], ratings_by_team[away]
    league = sum((r["off_ppd"]+r["def_ppd_allowed"])/2 for r in ratings_by_team.values())/len(ratings_by_team)
    h_ppd = max(0, h["off_ppd"] + a["def_ppd_allowed"] - league)
    a_ppd = max(0, a["off_ppd"] + h["def_ppd_allowed"] - league)
    hp = h_ppd*expected_drives + home_edge_points/2
    ap = a_ppd*expected_drives - home_edge_points/2
    return {"home":home,"away":away,"home_points":round(hp,1),
            "away_points":round(ap,1),"home_margin":round(hp-ap,1),
            "total":round(hp+ap,1),
            "note":"Uncalibrated baseline, not a betting recommendation"}
