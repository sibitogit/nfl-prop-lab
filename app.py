import pandas as pd
import streamlit as st
import altair as alt
from datetime import datetime, timezone

st.set_page_config(
    page_title="NFL Prop Lab — Candidate v0.7",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)

PLAYER_URL = "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{season}.csv"
SCHEDULE_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"

MARKETS = {
    "Passing Yards": "passing_yards",
    "Pass Completions": "completions",
    "Pass Attempts": "attempts",
    "Passing TDs": "passing_tds",
    "Interceptions Thrown": "passing_interceptions",
    "Rushing Yards": "rushing_yards",
    "Rush Attempts": "carries",
    "Rushing TDs": "rushing_tds",
    "Receptions": "receptions",
    "Receiving Yards": "receiving_yards",
    "Targets": "targets",
    "Receiving TDs": "receiving_tds",
}

POSITION_MARKETS = {
    "QB": ["Passing Yards","Pass Completions","Pass Attempts","Passing TDs",
           "Interceptions Thrown","Rushing Yards","Rush Attempts","Rushing TDs"],
    "RB": ["Rushing Yards","Rush Attempts","Rushing TDs","Receptions",
           "Receiving Yards","Targets","Receiving TDs"],
    "WR": ["Receptions","Receiving Yards","Targets","Receiving TDs",
           "Rushing Yards","Rush Attempts","Rushing TDs"],
    "TE": ["Receptions","Receiving Yards","Targets","Receiving TDs"],
}

SEASONS = [2022, 2023, 2024, 2025, 2026]
MIN_SPLIT_GAMES = 3

@st.cache_data(ttl=3600, show_spinner=False)
def load_player_season(season):
    df = pd.read_csv(PLAYER_URL.format(season=season), low_memory=False)
    return df[df["season_type"].eq("REG")].copy()

@st.cache_data(ttl=300, show_spinner=False)
def load_schedule():
    games = pd.read_csv(SCHEDULE_URL, low_memory=False)
    return games[games["game_type"].eq("REG")].copy()

@st.cache_data(ttl=3600, show_spinner=False)
def load_all():
    frames, failures = [], []
    for season in SEASONS:
        try:
            frames.append(load_player_season(season))
        except Exception as exc:
            failures.append((season, str(exc)))
    if not frames:
        raise RuntimeError("No player-stat files loaded.")
    return pd.concat(frames, ignore_index=True), failures

def add_home_away(player_df, games):
    if "game_id" in player_df.columns and "game_id" in games.columns:
        g = games[["game_id","away_team","home_team","gameday"]].drop_duplicates("game_id")
        x = player_df.merge(g, how="left", on="game_id")
        x["venue"] = "Unknown"
        x.loc[x["team"].eq(x["home_team"]), "venue"] = "Home"
        x.loc[x["team"].eq(x["away_team"]), "venue"] = "Away"
        return x.drop(columns=["away_team","home_team"])
    return player_df.assign(venue="Unknown", gameday=pd.NA)

from core import (
    grade_prop, record, hit_rate, hit_text, split_table,
    defense_vs_position, line_explorer, consistency_metrics,
)

# ---------- DATA ----------
st.title("🏈 NFL Prop Lab")
st.caption("Candidate v0.7 · historical prop research, not a betting recommendation")

try:
    with st.spinner("Loading NFL data…"):
        data, failures = load_all()
        schedule = load_schedule()
except Exception as exc:
    st.error("NFL data could not be loaded. Try again later.")
    with st.expander("Technical details"):
        st.exception(exc)
    st.stop()

required = {"player_id","player_display_name","position","season","week","team","opponent_team"}
missing = required.difference(data.columns)
if missing:
    st.error("The nflverse data structure changed and this build needs an update.")
    with st.expander("Technical details"):
        st.write("Missing fields:", sorted(missing))
    st.stop()

data = data[data["position"].isin(["QB","RB","WR","TE"])].copy()

# ---------- SIDEBAR / INPUT ----------
with st.sidebar:
    st.header("Prop setup")
    st.caption("Enter the line exactly as shown by your sportsbook.")

    players = (
        data[["player_id","player_display_name","position","season"]]
        .dropna()
        .sort_values("season")
        .drop_duplicates("player_id", keep="last")
        .sort_values("player_display_name")
    )

    labels = players.apply(lambda r: f"{r['player_display_name']} — {r['position']}", axis=1).tolist()
    player_label = st.selectbox("Player", labels, index=None, placeholder="Search a player…")

    if player_label is None:
        st.info("Choose a player to begin.")
        st.stop()

    player_name, player_pos = player_label.rsplit(" — ", 1)
    player_id = players.loc[
        (players["player_display_name"].eq(player_name)) & (players["position"].eq(player_pos)),
        "player_id"
    ].iloc[0]

    available_markets = [m for m in POSITION_MARKETS[player_pos] if MARKETS[m] in data.columns]
    market = st.selectbox("Market", available_markets)
    side = st.segmented_control("Side", ["Over","Under"], default="Over")

    stat = MARKETS[market]
    default_line = 0.5 if "TD" in market or "Interceptions" in market else 50.5
    step = 0.5
    line = st.number_input("Sportsbook line", min_value=0.0, value=float(default_line), step=step)

    scope = st.selectbox("Sample", ["Current season","Last 5","Last 10","Last 20"], index=2)

    teams = sorted(data["team"].dropna().unique())
    matchup_defense = st.selectbox("Upcoming opponent", ["Not selected"] + teams)

    st.divider()
    st.caption("W-L-P = Win · Loss · Push")
    if failures:
        st.warning("One or more season files are temporarily unavailable.")

# ---------- PLAYER HISTORY ----------
hist = data[data["player_id"].eq(player_id)].copy()
hist[stat] = pd.to_numeric(hist[stat], errors="coerce")
hist = hist.dropna(subset=[stat]).sort_values(["season","week"])
hist = add_home_away(hist, schedule)
hist = grade_prop(hist, stat, line, side)

if hist.empty:
    st.info("No usable games exist for this player/market.")
    st.stop()

latest_data_season = int(data["season"].max())
player_latest_season = int(hist["season"].max())
season_hist = hist[hist["season"].eq(player_latest_season)].copy()

last5, last10, last20 = hist.tail(5), hist.tail(10), hist.tail(20)
sample_map = {
    "Current season": season_hist,
    "Last 5": last5,
    "Last 10": last10,
    "Last 20": last20,
}
primary = sample_map[scope]

st.subheader(f"{player_name} · {side} {line:g} {market}")
st.caption(f"{player_pos} · latest player season in dataset: {player_latest_season}")

if player_latest_season < latest_data_season:
    st.warning(
        f"This player has no {latest_data_season} regular-season stat row in the current dataset. "
        f"The 'Current season' sample therefore refers to {player_latest_season}."
    )

# ---------- QUICK READ ----------
tab1, tab2, tab3 = st.tabs(["Quick read", "Matchup & splits", "Game log"])

with tab1:
    a,b,c,d,e = st.columns(5)
    a.metric(scope, hit_text(primary))
    b.metric("Last 5", hit_text(last5))
    c.metric("Last 10", hit_text(last10))
    d.metric("Average", f"{primary[stat].mean():.1f}")
    e.metric("Median", f"{primary[stat].median():.1f}")

    if len(primary) < 5:
        st.warning("Very small sample. Do not treat this hit rate as stable.")
    elif len(primary) < 10:
        st.info("Limited sample. Use it as context, not as a forecast.")

    st.markdown("#### Line explorer")
    st.caption("How sensitive is the historical result to a nearby sportsbook line?")
    explore = line_explorer(primary, stat, line, side)
    st.dataframe(
        explore,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Line": st.column_config.NumberColumn(format="%.1f"),
            "Hit rate": st.column_config.NumberColumn(format="%.1f%%"),
        }
    )

    cons = consistency_metrics(primary, stat)
    if cons:
        p1,p2,p3 = st.columns(3)
        p1.metric("25th percentile", f"{cons['P25']:.1f}")
        p2.metric("Median", f"{cons['P50']:.1f}")
        p3.metric("75th percentile", f"{cons['P75']:.1f}")
        st.caption(
            f"Observed range {cons['Min']:.1f}–{cons['Max']:.1f} · "
            f"standard deviation {cons['Std']:.1f}"
        )

    chart_df = primary[["season","week","opponent_team","venue",stat,"grade"]].copy()
    chart_df["Game"] = chart_df["season"].astype(str) + " W" + chart_df["week"].astype(int).astype(str)
    chart_df = chart_df.rename(columns={stat:"Result","opponent_team":"Opponent","venue":"Venue","grade":"Grade"})

    base = alt.Chart(chart_df).encode(
        x=alt.X("Game:N", sort=None, title="Game"),
        tooltip=["Game:N","Opponent:N","Venue:N","Grade:N",alt.Tooltip("Result:Q", format=".1f")]
    )
    bars = base.mark_bar().encode(y=alt.Y("Result:Q", title=market))
    rule = alt.Chart(pd.DataFrame({"line":[line]})).mark_rule(strokeDash=[6,4]).encode(y="line:Q")
    st.altair_chart((bars + rule).properties(height=330), use_container_width=True)

with tab2:
    st.markdown("#### Upcoming defensive matchup")
    if matchup_defense == "Not selected":
        st.info("Select the upcoming opponent in the sidebar to see defensive context.")
    else:
        # Defensive context uses the player's latest available season.
        def_ctx = defense_vs_position(data, player_latest_season, player_pos, stat)
        if def_ctx.empty or matchup_defense not in set(def_ctx["opponent_team"]):
            st.info(f"No {player_latest_season} defensive context is available for {matchup_defense}.")
        else:
            row = def_ctx.loc[def_ctx["opponent_team"].eq(matchup_defense)].iloc[0]
            league_avg = def_ctx["Allowed_per_game"].mean()
            delta = row["Allowed_per_game"] - league_avg
            rank = int(row["Most_allowed_rank"])
            total = len(def_ctx)

            x1,x2,x3,x4 = st.columns(4)
            x1.metric(f"Allowed to {player_pos}s / game", f"{row['Allowed_per_game']:.1f}",
                      f"{delta:+.1f} vs avg")
            x2.metric("Most-allowed rank", f"{rank}/{total}")
            x3.metric("Last 5 allowed / game", f"{row['L5_Allowed_per_game']:.1f}")
            x4.metric("League average", f"{league_avg:.1f}")

            st.caption(
                f"This sums {market.lower()} produced by all {player_pos}s facing {matchup_defense} "
                "in each game. It is matchup context, not a player projection."
            )

    st.markdown("#### Historical splits")
    s1,s2 = st.columns(2)
    with s1:
        venue_df = primary[primary["venue"].isin(["Home","Away"])]
        venue = split_table(venue_df, "venue", stat)
        st.markdown("**Home / Away**")
        if venue.empty:
            st.caption("No venue data available.")
        else:
            st.dataframe(venue, hide_index=True, use_container_width=True)
    with s2:
        opponents = split_table(primary, "opponent_team", stat)
        st.markdown("**Opponent**")
        st.dataframe(
            opponents.sort_values(["Games","Hit rate"], ascending=False),
            hide_index=True,
            use_container_width=True
        )
        st.caption("Opponent rows with fewer than 3 games are marked Small.")

with tab3:
    cols = ["season","week","gameday","team","opponent_team","venue",stat,"grade"]
    view = hist[[c for c in cols if c in hist.columns]].copy()
    view = view.rename(columns={
        "season":"Season","week":"Week","gameday":"Date","team":"Team",
        "opponent_team":"Opponent","venue":"Venue",stat:market,"grade":"Grade"
    })
    st.dataframe(
        view.sort_values(["Season","Week"], ascending=False),
        hide_index=True,
        use_container_width=True
    )

st.divider()
st.caption(
    "NFL Prop Lab uses nflverse weekly player statistics and schedules. "
    "Historical results, hit rates and matchup allowances are descriptive and do not establish expected value "
    "or predict future outcomes. Sportsbook lines are entered manually."
)
st.caption(f"Session data loaded: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
