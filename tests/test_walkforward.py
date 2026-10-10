import csv
from scripts.walkforward import evaluate

def test_walkforward_no_future_leakage(tmp_path):
    drives=tmp_path/"drives.csv"
    with drives.open("w",newline="") as f:
        w=csv.writer(f)
        w.writerow(["game_id","game_date","team","opponent","drive_id","offensive_points","overtime"])
        for n in range(12):
            w.writerow(["old","2026-09-01","A","B",str(n),7,"false"])
            w.writerow(["old","2026-09-01","B","A",str(n),0,"false"])
        for n in range(12):
            w.writerow(["future","2026-10-10","A","B",str(n),0,"false"])
    games=tmp_path/"games.csv"
    games.write_text("game_date,home,away,home_score,away_score,closing_home_spread,closing_total\n2026-10-10,A,B,35,7,-7,48\n")
    result=evaluate(drives,games)
    assert result["games_evaluated"]==1
    assert result["predictions"][0]["model_margin"]>0

def test_walkforward_pass_on_insufficient_data(tmp_path):
    drives=tmp_path/"drives.csv"
    drives.write_text("game_id,game_date,team,opponent,drive_id,offensive_points,overtime\n")
    games=tmp_path/"games.csv"
    games.write_text("game_date,home,away,home_score,away_score,closing_home_spread,closing_total\n2026-10-10,A,B,35,7,-7,48\n")
    assert evaluate(drives,games)["games_evaluated"]==0
