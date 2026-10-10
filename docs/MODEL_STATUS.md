# 2026 CFB model status

## Implemented
- ESPN completed-score collector and scheduled GitHub Actions artifact
- Score integrity audit and unit tests
- Strictly 2026, pregame-date-filtered, non-overtime drive CSV loader
- Shrunk offensive and defensive points per drive and a baseline matchup projection

## Not yet implemented or verified
- Drive-by-drive ingestion and scoring classification from an authoritative source
- Drive possession ownership, safety/defensive TD/PAT classification and first-half splits
- Opponent-strength adjustment, pace estimation, injury and roster verification
- Walk-forward validation against historical market closing lines
- Calibration, probabilities, no-vig EV, actionable betting picks

**Do not feed final scores into the drive model as offensive points.**
No profitability claims. The drive model requires independently verified drive-level data.
