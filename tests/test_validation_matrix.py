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

from core import sample_comparison, line_sample_matrix, season_breakdown

def test_sample_comparison_windows():
    df = pd.DataFrame({
        "season":[2024]*4 + [2025]*6,
        "week":list(range(1,5))+list(range(1,7)),
        "receiving_yards":[30,40,50,60,70,80,90,100,110,120],
    })
    g = grade_prop(df, "receiving_yards", 74.5, "Over")
    out = sample_comparison(g, "receiving_yards", 2025)
    assert out["Sample"].tolist() == ["Latest season (2025)", "Last 5", "Last 10", "Last 20", "All loaded games"]
    assert int(out.loc[out["Sample"].eq("Last 5"), "Games"].iloc[0]) == 5


def test_line_sample_matrix_changes_by_line():
    df = pd.DataFrame({
        "season":[2025]*5,
        "week":[1,2,3,4,5],
        "receptions":[3,4,5,6,7],
    })
    g = grade_prop(df, "receptions", 4.5, "Over")
    out = line_sample_matrix(g, "receptions", [3.5,4.5,5.5], "Over", 2025)
    assert out["Line"].tolist() == [3.5,4.5,5.5]
    assert out.loc[out["Line"].eq(3.5), "L5"].iloc[0] > out.loc[out["Line"].eq(5.5), "L5"].iloc[0]


def test_season_breakdown():
    df = pd.DataFrame({
        "season":[2024,2024,2025,2025],
        "week":[1,2,1,2],
        "targets":[4,8,6,10],
    })
    g = grade_prop(df, "targets", 5.5, "Over")
    out = season_breakdown(g, "targets")
    assert out["Season"].tolist() == [2025, 2024]
    assert out["Games"].tolist() == [2,2]
