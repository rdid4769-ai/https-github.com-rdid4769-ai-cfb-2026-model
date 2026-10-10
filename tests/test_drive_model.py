import csv
import pytest
from scripts.drive_model import load_drives, ratings, project

def test_cutoff_and_overtime(tmp_path):
    p=tmp_path/"drives.csv"
    fields=["game_id","game_date","team","opponent","drive_id","offensive_points","overtime"]
    rows=[
        ["1","2026-09-05","A","B","1","7","false"],
        ["1","2026-09-05","B","A","1","0","false"],
        ["1","2026-09-05","A","B","2","6","true"],
        ["2","2026-10-10","A","B","1","7","false"]]
    with p.open("w",newline="") as f:
        w=csv.writer(f);w.writerow(fields);w.writerows(rows)
    valid=load_drives(p,"2026-10-10")
    assert len(valid)==2
    assert valid[0]["offensive_points"]==7

def test_no_old_season(tmp_path):
    p=tmp_path/"drives.csv"
    p.write_text("game_id,game_date,team,opponent,drive_id,offensive_points\\n1,2025-09-01,A,B,1,7\\n".replace("\\n","\n"))
    with pytest.raises(ValueError,match="Non-2026"):
        load_drives(p,"2026-10-10")

def test_projection():
    r={"A":{"off_ppd":2.5,"def_ppd_allowed":1.7},
       "B":{"off_ppd":2.1,"def_ppd_allowed":2.4}}
    x=project("A","B",r)
    assert x["home_margin"]>0
    assert x["total"]==round(x["home_points"]+x["away_points"],1)
