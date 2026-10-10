import csv
import pytest
from scripts.audit_scores import audit

def test_audit_rejects_non_2026(tmp_path):
    p = tmp_path / "scores.csv"
    with p.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "game_id", "kickoff_utc", "home_team", "away_team", "home_score", "away_score"])
        writer.writeheader()
        writer.writerow({"game_id":"1","kickoff_utc":"2025-10-03T18:00Z",
                         "home_team":"A","away_team":"B","home_score":"21","away_score":"14"})
    with pytest.raises(ValueError, match="Non-2026"):
        audit(p)
