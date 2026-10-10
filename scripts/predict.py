"""Pregame 2026-only baseline predictions from verified offensive-drive CSV.

No odds, injury adjustments or claim of calibrated probabilities.
"""
import argparse
import csv
from pathlib import Path
from scripts.drive_model import load_drives, ratings, project

def predict_file(drives_path, matchups_path, output_path, as_of):
    drive_rows = load_drives(drives_path, as_of)
    team_ratings = ratings(drive_rows)
    if not team_ratings:
        raise ValueError("Insufficient verified pregame drives for projections")
    with Path(matchups_path).open(newline="") as f:
        matchups = list(csv.DictReader(f))
    if not {"home","away"}.issubset(matchups[0] if matchups else {}):
        raise ValueError("Matchups need home,away columns")
    results=[]
    for matchup in matchups:
        h,a=matchup["home"],matchup["away"]
        if h not in team_ratings or a not in team_ratings:
            results.append({"home":h,"away":a,"status":"PASS: insufficient verified drive data"})
            continue
        row=project(h,a,team_ratings)
        row["status"]="UNCALIBRATED: not a betting pick"
        results.append(row)
    output_path=Path(output_path)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    with output_path.open("w",newline="") as f:
        fields=["home","away","home_points","away_points","home_margin","total","note","status"]
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    return results

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--drives",required=True)
    p.add_argument("--matchups",required=True)
    p.add_argument("--as-of",required=True,help="YYYY-MM-DD game date; strictly prior games only")
    p.add_argument("--output",default="output/predictions.csv")
    a=p.parse_args()
    print(predict_file(a.drives,a.matchups,a.output,a.as_of))
