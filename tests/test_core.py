import pandas as pd
from core import grade_prop, record, hit_rate, line_explorer, consistency_metrics, defense_vs_position

def test_push_and_hit_rate():
    df=pd.DataFrame({"receiving_yards":[49.0,50.0,51.0]})
    g=grade_prop(df,"receiving_yards",50.0,"Over")
    assert g["grade"].tolist()==["Loss","Push","Win"]
    assert record(g)=="1-1-1"
    assert hit_rate(g)==50.0

def test_under():
    df=pd.DataFrame({"receptions":[3,4,5]})
    assert grade_prop(df,"receptions",4,"Under")["grade"].tolist()==["Win","Push","Loss"]

def test_line_explorer_count_offsets():
    df=pd.DataFrame({"receptions":[3,4,5,6]})
    assert line_explorer(df,"receptions",4.5,"Over")["Line"].tolist()==[2.5,3.5,4.5,5.5,6.5]

def test_consistency():
    c=consistency_metrics(pd.DataFrame({"passing_yards":[100,200,300,400]}),"passing_yards")
    assert c["P50"]==250.0 and c["Min"]==100.0 and c["Max"]==400.0

def test_defense_position_group_aggregation():
    df=pd.DataFrame({"season":[2025]*6,"week":[1,1,2,2,1,2],"game_id":["g1","g1","g2","g2","g3","g4"],"position":["WR"]*6,"opponent_team":["BUF","BUF","BUF","BUF","MIA","MIA"],"receiving_yards":[40,60,30,70,50,70]})
    out=defense_vs_position(df,2025,"WR","receiving_yards").set_index("opponent_team")
    assert out.loc["BUF","Allowed_per_game"]==100.0
    assert out.loc["MIA","Allowed_per_game"]==60.0
    assert out.loc["BUF","Most_allowed_rank"]==1
