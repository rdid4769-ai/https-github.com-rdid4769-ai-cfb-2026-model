"""Collect ESPN raw drive records for completed 2026 games.

Raw possessions are NOT automatically labeled offensive points. ESPN drive
summary scoring fields alone may include defensive scores, so classification
requires play-by-play validation before model training.
"""
import argparse
import csv
import json
from pathlib import Path
import requests

SUMMARY = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/summary"

def extract_drives(payload, game_id):
    drives = payload.get("drives") or {}
    previous = drives.get("previous") or []
    result = []
    for drive in previous:
        team = drive.get("team") or {}
        result.append({
            "game_id":str(game_id),
            "drive_id":str(drive.get("id") or ""),
            "team_id":str(team.get("id") or ""),
            "team_name":str(team.get("displayName") or team.get("name") or ""),
            "description":str(drive.get("description") or ""),
            "result":str(drive.get("displayResult") or ""),
            "start_period":str((drive.get("start") or {}).get("period", {}).get("number") or ""),
            "end_period":str((drive.get("end") or {}).get("period", {}).get("number") or ""),
            "plays":str(drive.get("offensivePlays") or ""),
            "raw_json":json.dumps(drive, separators=(",",":"))
        })
    return result

def collect(scores_csv, output_dir, max_games=0):
    output_dir.mkdir(parents=True,exist_ok=True)
    with scores_csv.open(newline="") as f:
        games=list(csv.DictReader(f))
    if not games or any(not x["kickoff_utc"].startswith("2026-") for x in games):
        raise ValueError("Expected nonempty 2026 scores input")
    if max_games:
        games=games[:max_games]
    rows=[]
    errors=[]
    session=requests.Session()
    for game in games:
        gid=game["game_id"]
        try:
            response=session.get(SUMMARY,params={"event":gid},timeout=30)
            response.raise_for_status()
            payload=response.json()
            extracted=extract_drives(payload,gid)
            if not extracted:
                errors.append({"game_id":gid,"reason":"no previous drives"})
            rows.extend(extracted)
        except (requests.RequestException,ValueError) as exc:
            errors.append({"game_id":gid,"reason":str(exc)})
    path=output_dir/"raw_2026_drives.csv"
    fields=["game_id","drive_id","team_id","team_name","description","result",
            "start_period","end_period","plays","raw_json"]
    with path.open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (output_dir/"drive_collection_status.json").write_text(json.dumps({
        "games_requested":len(games),"raw_drives":len(rows),
        "games_with_errors":len(errors),"errors":errors,
        "offensive_points_verified":False,
        "warning":"Raw drives cannot be used as offensive PPD without play-level scoring verification."
    },indent=2))
    if not rows:
        raise RuntimeError("No raw drives retrieved; inspect drive_collection_status.json")
    print(f"Collected {len(rows)} raw drives from {len(games)} games; {len(errors)} missing/failed")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--scores",default="output/completed_2026_scores.csv")
    parser.add_argument("--output-dir",default="output")
    parser.add_argument("--max-games",type=int,default=0)
    args=parser.parse_args()
    collect(Path(args.scores),Path(args.output_dir),args.max_games)
