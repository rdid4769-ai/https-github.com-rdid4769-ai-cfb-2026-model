from scripts.refresh_scores import normalize

def test_completed_2026_only():
    event = {"id":"123","date":"2026-10-03T18:00Z","status":{"type":{"completed":True}},
             "competitions":[{"competitors":[
                {"homeAway":"home","team":{"displayName":"Home"},"score":"21"},
                {"homeAway":"away","team":{"displayName":"Away"},"score":"14"}]}]}
    assert normalize(event)["home_score"] == 21
    event["status"]["type"]["completed"] = False
    assert normalize(event) is None
    event["status"]["type"]["completed"] = True
    event["date"] = "2025-10-03T18:00Z"
    assert normalize(event) is None
