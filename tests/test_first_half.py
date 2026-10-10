import pytest
from scripts.first_half import first_half_projection

def test_rejects_missing_half():
    with pytest.raises(ValueError,match="Half field"):
        first_half_projection([{"team":"A","opponent":"B","offensive_points":7}],"A","B")

def test_first_half_projection():
    rows=[]
    for n in range(12):
        rows.append({"team":"A","opponent":"B","offensive_points":7.0,"half":"1"})
        rows.append({"team":"B","opponent":"A","offensive_points":0.0,"half":"1"})
    x=first_half_projection(rows,"A","B")
    assert x["home_margin"]>0
    assert "1H" in x["note"]
