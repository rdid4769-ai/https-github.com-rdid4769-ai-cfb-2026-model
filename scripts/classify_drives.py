"""Conservative play-by-play scoreboard classifier for 2026 offensive drives.

Input: raw_2026_drives.csv and completed_2026_scores.csv.
Only games whose entire sequential scoreboard passes integrity checks are used.
Uncertain scoring events are excluded, never silently counted as offense.
"""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

OFFENSIVE_TD = {"Rushing Touchdown", "Passing Touchdown", "Pass Reception", "Rush"}
NONOFFENSIVE_TD = {"Interception Return Touchdown", "Punt Return Touchdown",
                   "Fumble Return Touchdown", "Kickoff Return Touchdown",
                   "Blocked Punt Touchdown", "Blocked Field Goal Touchdown",
                   "Defensive 2pt Conversion"}

def classify(raw_path, scores_path, output_path, report_path):
    games = {r["game_id"]: r for r in csv.DictReader(open(scores_path, newline=""))}
    grouped = defaultdict(list)
    for r in csv.DictReader(open(raw_path, newline="")):
        grouped[r["game_id"]].append(r)
    out = []
    stats = Counter()
    for gid, drives in grouped.items():
        game = games.get(gid)
        if not game:
            stats["unknown_games"] += 1
            continue
        plays = {}
        for drive in drives:
            for p in json.loads(drive["raw_json"]).get("plays", []):
                if p.get("id") and p.get("sequenceNumber") is not None:
                    plays[str(p["id"])] = p
        ordered = sorted(plays.values(), key=lambda p: int(p["sequenceNumber"]))
        away = home = 0
        deltas = {}
        valid = True
        for p in ordered:
            if "awayScore" not in p or "homeScore" not in p:
                continue
            a, h = int(p["awayScore"]), int(p["homeScore"])
            da, dh = a-away, h-home
            if da < 0 or dh < 0 or (da and dh) or max(da, dh) > 9:
                valid = False
                break
            deltas[str(p["id"])] = (da, dh)
            away, home = a, h
        if not valid or (away, home) != (int(game["away_score"]), int(game["home_score"])):
            stats["excluded_games_scoreboard_integrity"] += 1
            continue
        stats["matched_games"] += 1
        for d in drives:
            team = d["team_name"]
            if team == game["home_team"]:
                side = "home"
                opponent = game["away_team"]
            elif team == game["away_team"]:
                side = "away"
                opponent = game["home_team"]
            else:
                stats["unmatched_team_drives"] += 1
                continue
            raw = json.loads(d["raw_json"])
            period = int((raw.get("start", {}).get("period") or {}).get("number") or 0)
            if period not in (1, 2, 3, 4):
                stats["overtime_or_unknown_period_drives"] += 1
                continue
            points = 0
            ambiguous = False
            for p in raw.get("plays", []):
                da, dh = deltas.get(str(p.get("id")), (0, 0))
                if not (da or dh):
                    continue
                own, opp = (dh, da) if side == "home" else (da, dh)
                typ = (p.get("type") or {}).get("text", "")
                text = str(p.get("text", "")).upper()
                if own == 3 and not opp and typ == "Field Goal Good":
                    points += 3
                elif own in (6, 7, 8) and not opp and typ in OFFENSIVE_TD and not any(w in text for w in ("INTERCEPT", "FUMBLE", "RETURN")):
                    points += own
                elif opp and not own and (typ in NONOFFENSIVE_TD or typ == "Safety" or any(w in text for w in ("INTERCEPT", "FUMBLE", "RETURN"))):
                    pass
                elif own and not opp and typ in NONOFFENSIVE_TD:
                    pass
                else:
                    ambiguous = True
            if ambiguous or points > 8:
                stats["ambiguous_drives"] += 1
                continue
            out.append({"game_id": gid, "game_date": game["kickoff_utc"][:10],
                        "team": team, "opponent": opponent, "drive_id": d["drive_id"],
                        "offensive_points": points, "half": "1" if period <= 2 else "2",
                        "overtime": "false"})
            stats["classified_drives"] += 1
            stats["offensive_points"] += points
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        fields = ["game_id", "game_date", "team", "opponent", "drive_id",
                  "offensive_points", "half", "overtime"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out)
    Path(report_path).write_text(json.dumps({
        "counts": dict(stats),
        "status": "PARTIAL COVERAGE - NOT INDEPENDENTLY VALIDATED",
        "warning": "Excluded scoreboard-inconsistent games. Not a calibrated betting model."
    }, indent=2))
    return dict(stats)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--raw", required=True)
    p.add_argument("--scores", required=True)
    p.add_argument("--output", default="output/verified_2026_drives.csv")
    p.add_argument("--report", default="output/scoring_report.json")
    args = p.parse_args()
    print(classify(args.raw, args.scores, args.output, args.report))
