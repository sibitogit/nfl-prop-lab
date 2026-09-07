import pandas as pd
from core import grade_prop, hit_rate, record, consistency_metrics, defense_vs_position

def test_qb_passing_yards_over_and_under():
    df = pd.DataFrame({"passing_yards":[180, 249, 250, 300]})
    over = grade_prop(df, "passing_yards", 249.5, "Over")
    under = grade_prop(df, "passing_yards", 249.5, "Under")
    assert record(over) == "2-2-0"
    assert record(under) == "2-2-0"

def test_rb_rushing_push():
    df = pd.DataFrame({"rushing_yards":[40, 59.5, 80]})
    g = grade_prop(df, "rushing_yards", 59.5, "Over")
    assert record(g) == "1-1-1"
    assert hit_rate(g) == 50.0

def test_wr_receptions():
    df = pd.DataFrame({"receptions":[3,4,5,6,8]})
    g = grade_prop(df, "receptions", 4.5, "Over")
    assert record(g) == "3-2-0"
    assert hit_rate(g) == 60.0

def test_te_receiving_yards_under():
    df = pd.DataFrame({"receiving_yards":[20,30,39,40,55]})
    g = grade_prop(df, "receiving_yards", 39.5, "Under")
    assert record(g) == "3-2-0"

def test_consistency_median():
    df = pd.DataFrame({"targets":[2,4,6,8,10]})
    c = consistency_metrics(df, "targets")
    assert c["P50"] == 6.0

def test_defense_aggregation_multiple_players_same_game():
    df = pd.DataFrame({
        "season":[2025]*4,
        "position":["WR"]*4,
        "opponent_team":["DAL"]*4,
        "game_id":["g1","g1","g2","g2"],
        "receiving_yards":[60,40,50,30],
    })
    out = defense_vs_position(df, 2025, "WR", "receiving_yards")
    row = out.iloc[0]
    assert row["Allowed_per_game"] == 90.0
