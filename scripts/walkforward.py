"""Walk-forward evaluation of 2026-only verified-drive baseline against market lines.

Inputs:
  verified drives: game_id,game_date,team,opponent,drive_id,offensive_points,overtime
  historical games: game_date,home,away,home_score,away_score,closing_home_spread,closing_total
Each game is predicted using strictly earlier drive data; never training on its result.
"""
import argparse
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from scripts.drive_model import load_drives, ratings, project

FIELDS = {"game_date", "home", "away", "home_score", "away_score",
          "closing_home_spread", "closing_total"}

def evaluate(drives_csv, games_csv, min_drives=10):
    with Path(games_csv).open(newline="") as f:
        reader=csv.DictReader(f)
        if not FIELDS.issubset(reader.fieldnames or []):
            raise ValueError("Missing historical game fields")
        games=list(reader)
    results=[]
    for game in sorted(games,key=lambda x:x["game_date"]):
        game_day=date.fromisoformat(game["game_date"][:10])
        if game_day.year != 2026:
            raise ValueError("Historical games must be from 2026")
        rows=load_drives(drives_csv,game_day.isoformat())
        r=ratings(rows,min_drives=min_drives)
        home,away=game["home"],game["away"]
        if home not in r or away not in r:
            continue
        pred=project(home,away,r)
        actual_margin=float(game["home_score"])-float(game["away_score"])
        actual_total=float(game["home_score"])+float(game["away_score"])
        market_margin=-float(game["closing_home_spread"])
        market_total=float(game["closing_total"])
        results.append({
            "game_date":game_day.isoformat(),"home":home,"away":away,
            "model_margin":pred["home_margin"],"actual_margin":actual_margin,
            "market_margin":market_margin,"model_total":pred["total"],
            "actual_total":actual_total,"market_total":market_total})
    if not results:
        return {"games_evaluated":0,"status":"INSUFFICIENT VERIFIED HISTORICAL DATA",
                "warning":"No betting edge established"}
    n=len(results)
    avg=lambda key:round(sum(abs(x[key]) for x in results)/n,3)
    return {
        "games_evaluated":n,
        "model_spread_mae":avg("model_spread_error") if False else round(sum(abs(x["model_margin"]-x["actual_margin"]) for x in results)/n,3),
        "market_spread_mae":round(sum(abs(x["market_margin"]-x["actual_margin"]) for x in results)/n,3),
        "model_total_mae":round(sum(abs(x["model_total"]-x["actual_total"]) for x in results)/n,3),
        "market_total_mae":round(sum(abs(x["market_total"]-x["actual_total"]) for x in results)/n,3),
        "winner_accuracy":round(sum((x["model_margin"]>0)==(x["actual_margin"]>0) for x in results)/n,3),
        "status":"UNVALIDATED BASELINE: evaluate coverage and calibration before wagering",
        "warning":"No ROI or EV without timestamped available prices and a calibrated probability model",
        "predictions":results}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--drives",required=True)
    p.add_argument("--games",required=True)
    p.add_argument("--output",default="output/walkforward.json")
    a=p.parse_args()
    result=evaluate(a.drives,a.games)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!="predictions"},indent=2))
