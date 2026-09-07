# NFL Prop Lab — Candidate v0.8

Correction build based on the first live Streamlit screenshots.

## Fixed
- Market-specific default lines instead of a universal 50.5:
  - Passing Yards 249.5
  - Receptions 4.5
  - Receiving Yards 54.5
  - Passing TDs 1.5
  - TD / INT markets 0.5
  - etc.
- Default line automatically resets when the market changes.
- Sample selector says exactly which season exists: `Latest season (2025)` rather than misleading `Current season`.
- 2026 not-yet-published data is shown as an informational notice rather than a technical warning.
- Quick-read KPI cards no longer duplicate "Last 10".
- W-L-P record moved out of narrow metric cards so `10-0-0` does not get visually clipped.
- Line Explorer ranges now depend on market:
  - Passing Yards: broader
  - Receiving/Rushing Yards: medium
  - Receptions: ±1/±2
  - TD/INT: half/one-unit movements
- No new commercial or predictive features added; this is deliberately a correction/UX build.

## Deployment
Replace the existing repo files with this build. Streamlit Community Cloud should redeploy automatically after the GitHub commit.
