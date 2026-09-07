import pandas as pd

def pct(n, d):
    return 0.0 if d == 0 else 100.0 * n / d

def grade_prop(df, stat, line, side):
    x = df.copy()
    values = pd.to_numeric(x[stat], errors="coerce")
    x = x.loc[values.notna()].copy()
    values = pd.to_numeric(x[stat], errors="coerce")
    if side == "Over":
        x["grade"] = "Loss"
        x.loc[values > line, "grade"] = "Win"
    elif side == "Under":
        x["grade"] = "Loss"
        x.loc[values < line, "grade"] = "Win"
    else:
        raise ValueError("side must be Over or Under")
    x.loc[values == line, "grade"] = "Push"
    return x

def record(frame):
    if frame.empty:
        return "0-0-0"
    counts = frame["grade"].value_counts()
    return f"{int(counts.get('Win',0))}-{int(counts.get('Loss',0))}-{int(counts.get('Push',0))}"

def hit_rate(frame):
    if frame.empty:
        return 0.0
    graded = frame[frame["grade"].isin(["Win","Loss"])]
    if graded.empty:
        return 0.0
    return 100.0 * graded["grade"].eq("Win").sum() / len(graded)

def hit_text(frame):
    return f"{hit_rate(frame):.0f}% · {record(frame)}"

def split_table(df, group_col, stat, min_games=3):
    rows=[]
    for key,g in df.groupby(group_col, dropna=False):
        vals=pd.to_numeric(g[stat], errors="coerce")
        rows.append({group_col:key,"Games":len(g),"Record":record(g),"Hit rate":round(hit_rate(g),1),"Average":round(vals.mean(),1),"Median":round(vals.median(),1),"Sample":"OK" if len(g)>=min_games else "Small"})
    return pd.DataFrame(rows)

def defense_vs_position(data, season, position, stat):
    x=data[data["season"].eq(season)&data["position"].eq(position)&data[stat].notna()].copy()
    if x.empty:
        return pd.DataFrame()
    keys=["season","week","opponent_team"]
    if "game_id" in x.columns:
        keys.append("game_id")
    game_allowed=x.groupby(keys,as_index=False)[stat].sum().rename(columns={stat:"allowed"})
    season_allowed=game_allowed.groupby("opponent_team",as_index=False).agg(Games=("allowed","size"),Allowed_per_game=("allowed","mean"),Median_allowed=("allowed","median"))
    season_allowed["Most_allowed_rank"]=season_allowed["Allowed_per_game"].rank(method="min",ascending=False).astype(int)
    last5=(game_allowed.sort_values(["opponent_team","week"]).groupby("opponent_team",group_keys=False).tail(5).groupby("opponent_team",as_index=False).agg(L5_Games=("allowed","size"),L5_Allowed_per_game=("allowed","mean")))
    return season_allowed.merge(last5,on="opponent_team",how="left")

def line_explorer(df, stat, main_line, side):
    small={"completions","attempts","passing_tds","passing_interceptions","carries","rushing_tds","receptions","targets","receiving_tds"}
    offsets=[-2,-1,0,1,2] if stat in small else [-10,-5,0,5,10]
    rows=[]
    for off in offsets:
        test_line=max(0.0, main_line+off)
        g=grade_prop(df,stat,test_line,side)
        rows.append({"Line":float(test_line),"Hit rate":round(hit_rate(g),1),"Record":record(g),"Selected":"← sportsbook" if off==0 else ""})
    return pd.DataFrame(rows)

def consistency_metrics(df, stat):
    s=pd.to_numeric(df[stat],errors="coerce").dropna()
    if s.empty:
        return {}
    return {"P25":float(s.quantile(.25)),"P50":float(s.quantile(.50)),"P75":float(s.quantile(.75)),"Min":float(s.min()),"Max":float(s.max()),"Std":float(s.std(ddof=0)) if len(s)>1 else 0.0}
