from scripts.collect_drives import extract_drives

def test_extract_drives_no_score_assumption():
    data={"drives":{"previous":[{"id":"d1","team":{"id":"10","displayName":"Example"},
           "displayResult":"Touchdown","start":{"period":{"number":1}},
           "end":{"period":{"number":1}}}]}}
    rows=extract_drives(data,"123")
    assert len(rows)==1
    assert rows[0]["team_id"]=="10"
    assert "offensive_points" not in rows[0]
