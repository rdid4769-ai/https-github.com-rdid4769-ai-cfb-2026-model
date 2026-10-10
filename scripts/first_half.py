"""First-half 2026 model using verified, explicitly labeled regulation drives."""
from scripts.drive_model import ratings, project

def first_half_projection(rows, home, away, expected_drives_per_team=5.5,
                          home_edge_points=1.0):
    if not rows:
        raise ValueError("No verified drives")
    if any("half" not in r or not str(r["half"]).strip() for r in rows):
        raise ValueError("Half field required for every drive; cannot infer")
    first_half=[]
    for row in rows:
        if str(row["half"]).strip() not in ("1","2"):
            raise ValueError("Half must be 1 or 2")
        if str(row["half"]).strip()=="1":
            first_half.append(row)
    team_ratings=ratings(first_half,min_drives=5)
    if home not in team_ratings or away not in team_ratings:
        raise ValueError("Insufficient verified first-half possessions")
    out=project(home,away,team_ratings,
                expected_drives=expected_drives_per_team,
                home_edge_points=home_edge_points)
    out["note"]="Uncalibrated 1H baseline using verified first-half drives only"
    return out
