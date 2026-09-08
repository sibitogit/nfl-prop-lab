import pandas as pd
import streamlit as st
import altair as alt
from datetime import datetime, timezone

from core import (
    grade_prop, record, hit_rate, hit_text, split_table,
    defense_vs_position, line_explorer, consistency_metrics, sample_comparison, line_sample_matrix, season_breakdown,
)

st.set_page_config(
    page_title="NFL Prop Lab FREE — v1.0.1",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown("""
<style>
.block-container {padding-top: 2.2rem; padding-bottom: 2rem;}
[data-testid="stMetricValue"] {font-size: 2rem;}
[data-testid="stSidebar"] hr {margin-top: 1.25rem; margin-bottom: 1.25rem;}
div[data-testid="stAlert"] {border-radius: 0.65rem;}
</style>
""", unsafe_allow_html=True)


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

# Neutral starting points only. The user always replaces these with the sportsbook line.
DEFAULT_LINES = {
    "Passing Yards": 249.5,
    "Pass Completions": 21.5,
    "Pass Attempts": 32.5,
    "Passing TDs": 1.5,
    "Interceptions Thrown": 0.5,
    "Rushing TDs": 0.5,
    "Receptions": 4.5,
    "Receiving Yards": 54.5,
    "Targets": 6.5,
    "Receiving TDs": 0.5,
}

POSITION_DEFAULT_LINES = {
    ("QB", "Rushing Yards"): 24.5,
    ("QB", "Rush Attempts"): 4.5,
    ("RB", "Rushing Yards"): 59.5,
    ("RB", "Rush Attempts"): 13.5,
    ("WR", "Rushing Yards"): 4.5,
    ("WR", "Rush Attempts"): 0.5,
}

def default_line(position, market):
    return POSITION_DEFAULT_LINES.get((position, market), DEFAULT_LINES.get(market, 0.5))

SEASONS = [2022, 2023, 2024, 2025, 2026]

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

def explorer_offsets(market):
    if market in {"Passing Yards"}:
        return [-25, -10, 0, 10, 25]
    if market in {"Receiving Yards", "Rushing Yards"}:
        return [-10, -5, 0, 5, 10]
    if market in {"Pass Attempts", "Pass Completions", "Rush Attempts", "Targets"}:
        return [-4, -2, 0, 2, 4]
    if market == "Receptions":
        return [-2, -1, 0, 1, 2]
    if market in {"Passing TDs", "Interceptions Thrown", "Rushing TDs", "Receiving TDs"}:
        return [-1, -0.5, 0, 0.5, 1]
    return [-10, -5, 0, 5, 10]

def custom_line_explorer(df, stat, main_line, side, market):
    rows = []
    seen = set()
    td_int_markets = {
        "Passing TDs", "Interceptions Thrown", "Rushing TDs", "Receiving TDs"
    }
    for off in explorer_offsets(market):
        test_line = max(0.0, main_line + off)
        if market in td_int_markets:
            # Nearby alternate lines are most useful at sportsbook-style half increments.
            test_line = round(test_line * 2) / 2
        if test_line in seen:
            continue
        seen.add(test_line)
        g = grade_prop(df, stat, test_line, side)
        rows.append({
            "Line": float(test_line),
            "Hit rate": round(hit_rate(g), 1),
            "Record": record(g),
            "Selected": "← sportsbook" if abs(test_line - main_line) < 1e-9 else "",
        })
    return pd.DataFrame(rows)


def sample_quality(frame):
    n = len(frame)
    if n >= 15:
        return "Strong historical sample", "At least 15 games are included in the selected sample."
    if n >= 10:
        return "Usable historical sample", "10–14 games are included; splits may still be noisy."
    if n >= 5:
        return "Limited historical sample", "5–9 games are included; interpret percentages cautiously."
    return "Very small historical sample", "Fewer than 5 games are included; percentages are highly unstable."


def research_summary(frame, stat, line, side, last5=None):
    """Neutral descriptive summary for the selected historical sample."""
    if frame.empty:
        return []

    vals = pd.to_numeric(frame[stat], errors="coerce").dropna()
    if vals.empty:
        return []

    wins = int(frame["grade"].eq("Win").sum())
    losses = int(frame["grade"].eq("Loss").sum())
    pushes = int(frame["grade"].eq("Push").sum())
    games = len(frame)
    median = float(vals.median())
    average = float(vals.mean())

    if median > line:
        median_relation = "above"
    elif median < line:
        median_relation = "below"
    else:
        median_relation = "equal to"

    sentences = [
        f"{wins} historical hits in {games} games at this line ({hit_rate(frame):.0f}% graded hit rate; {wins}-{losses}-{pushes} W-L-P).",
        f"Sample average: {average:.1f}; median: {median:.1f}, {median_relation} the {line:g} line.",
    ]

    if last5 is not None and not last5.empty:
        recent = hit_rate(last5)
        overall = hit_rate(frame)
        diff = recent - overall
        if abs(diff) < 10:
            trend = "similar to"
        elif diff > 0:
            trend = "higher than"
        else:
            trend = "lower than"
        sentences.append(
            f"Last-5 graded hit rate is {recent:.0f}%, {trend} the selected sample's {overall:.0f}%."
        )

    return sentences

# ---------- DATA ----------
st.title("🏈 NFL Prop Lab FREE")
st.caption("Quick historical backtests for NFL player props.")
st.caption("FREE v1.0.1 · descriptive research only")

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
latest_loaded_season = int(data["season"].max())

# ---------- SIDEBAR ----------
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

    # Reset the starting line whenever the position/market context changes.
    # This prevents Streamlit from briefly carrying a stale or zero value
    # across players whose available prop menus differ.
    line_context = f"{player_pos}|{market}"
    if st.session_state.get("_line_context") != line_context:
        st.session_state["sportsbook_line"] = float(default_line(player_pos, market))
        st.session_state["_line_context"] = line_context

    line = st.number_input(
        "Sportsbook line",
        min_value=0.0,
        step=0.5,
        key="sportsbook_line",
        help="Starting value is only a neutral example. Replace it with your sportsbook's actual line."
    )

    # A true 0.0 line can be valid for some custom markets, but none of the
    # current default configurations use it. Keep user-entered 0.0 untouched;
    # context changes above will always initialize a proper default first.
    st.divider()
    st.caption("W-L-P = Win · Loss · Push")

# ---------- PLAYER HISTORY ----------
stat = MARKETS[market]
hist = data[data["player_id"].eq(player_id)].copy()
hist[stat] = pd.to_numeric(hist[stat], errors="coerce")
hist = hist.dropna(subset=[stat]).sort_values(["season","week"])
hist = add_home_away(hist, schedule)
hist = grade_prop(hist, stat, line, side)

if hist.empty:
    st.info("No usable games exist for this player/market.")
    st.stop()

player_latest_season = int(hist["season"].max())
season_hist = hist[hist["season"].eq(player_latest_season)].copy()
last5, last10, last20 = hist.tail(5), hist.tail(10), hist.tail(20)

# Treat an unavailable future/current season differently from a real technical error.
missing_seasons = sorted({s for s, _ in failures})
if 2026 in missing_seasons and latest_loaded_season < 2026:
    st.caption("Data status: 2026 regular-season player stats are not available yet; using the latest available historical season.")
elif failures:
    with st.expander("Data availability notice"):
        st.write("Some historical season files could not be loaded. The app is using all seasons that are currently available.")

# ---------- FREE EXPERIENCE ----------
# FREE is intentionally useful but bounded: it answers "how has this prop performed recently?"
# PRO is reserved for deeper windows, alternate-line analysis, matchup context, splits and exports.
free_sample = last5.copy()

st.subheader(f"{player_name} · {side} {line:g} {market}")
st.caption(f"{player_pos} · FREE v1.0.1 · latest available player season: {player_latest_season}")

tab1, tab2 = st.tabs(["Quick backtest", "Game log"])

with tab1:
    a,b,c,d = st.columns(4)
    a.metric("Last 5 hit rate", f"{hit_rate(free_sample):.0f}%")
    b.metric("Record", record(free_sample))
    c.metric("Average", f"{free_sample[stat].mean():.1f}")
    d.metric("Median", f"{free_sample[stat].median():.1f}")

    quality_title, quality_text = sample_quality(free_sample)
    st.caption(f"Sample quality: **{quality_title}** · {len(free_sample)} games · {quality_text}")

    st.markdown("#### Recent historical summary")
    summary_lines = research_summary(free_sample, stat, line, side, last5=free_sample)
    # Keep FREE concise: only the two core descriptive facts.
    for sentence in summary_lines[:2]:
        st.markdown(f"- {sentence}")

    st.caption(
        "Descriptive historical context only. It does not estimate win probability, expected value, or recommend a wager."
    )

    if len(free_sample) < 5:
        st.warning("Very small sample. Do not treat this hit rate as stable.")

    chart_df = free_sample[["season","week","opponent_team","venue",stat,"grade"]].copy()
    chart_df["Game"] = chart_df["season"].astype(str) + " W" + chart_df["week"].astype(int).astype(str)
    chart_df = chart_df.rename(columns={stat:"Result","opponent_team":"Opponent","venue":"Venue","grade":"Grade"})
    base = alt.Chart(chart_df).encode(
        x=alt.X("Game:N", sort=None, title="Game"),
        tooltip=["Game:N","Opponent:N","Venue:N","Grade:N",alt.Tooltip("Result:Q", format=".1f")]
    )
    bars = base.mark_bar().encode(y=alt.Y("Result:Q", title=market))
    rule = alt.Chart(pd.DataFrame({"line":[line]})).mark_rule(strokeDash=[6,4]).encode(y="line:Q")
    st.altair_chart((bars + rule).properties(height=330), use_container_width=True)

    st.markdown("#### Go deeper with PRO")
    st.caption(
        "FREE is built for a quick recent backtest. PRO unlocks the research tools that answer what happens "
        "when you widen the sample, move the line, split the games or add matchup context."
    )
    p1,p2,p3 = st.columns(3)
    p1.markdown("**More history 🔒**\n\nSeason · L10 · L20 · season-by-season")
    p2.markdown("**Line research 🔒**\n\nLine Explorer · alternate-line matrix · percentiles")
    p3.markdown("**Context 🔒**\n\nHome/Away · opponent splits · Defense vs Position")
    st.caption("PRO also includes the multi-sample Research Desk and CSV export.")

with tab2:
    cols = ["season","week","gameday","team","opponent_team","venue",stat,"grade"]
    view = free_sample[[c for c in cols if c in free_sample.columns]].copy()
    view = view.rename(columns={
        "season":"Season","week":"Week","gameday":"Date","team":"Team",
        "opponent_team":"Opponent","venue":"Venue",stat:market,"grade":"Grade"
    })
    st.dataframe(view.sort_values(["Season","Week"], ascending=False),
                 hide_index=True, use_container_width=True)
    st.caption("FREE game log shows the same Last-5 sample used by the quick backtest.")

st.divider()
with st.expander("How to read NFL Prop Lab FREE"):
    st.markdown(
        """
        **Hit rate** grades the player's last five available regular-season games against the line you entered. Pushes are excluded from the hit-rate denominator.

        **Average and median** summarize only those same five games.

        **Game log** lets you inspect each result behind the summary.

        NFL Prop Lab FREE is deliberately a recent-sample backtester. PRO adds larger samples, alternate-line analysis, historical splits, matchup context and export tools.
        """
    )

st.caption(
    "NFL Prop Lab uses nflverse weekly player statistics and schedules. Historical results and hit rates are "
    "descriptive and do not establish expected value or predict future outcomes. Sportsbook lines are entered manually."
)
st.caption(f"Session data loaded: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
