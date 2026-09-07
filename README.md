# NFL Prop Lab — Candidate v0.9 Beta

This build adds the first synthesis layer after the live v0.8 validation.

## New
- Neutral **Research summary** in Quick read.
- Shows wins/games, graded hit rate, W-L-P, average, median vs line, and Last-5 comparison.
- If an upcoming opponent is selected, the summary adds defense-vs-position rank and league-average context.
- Explicitly avoids calling a prop a "bet", "pick", "value", or "+EV".
- Added tests for summary logic, including push handling.

## Still unchanged
- Manual sportsbook line entry.
- Historical/descriptive analysis only.
- 2026 data loads automatically once the nflverse season file becomes available.
- No paid API, hosting upgrade, or new cost.

## Next checkpoint
Before commercialization, manually validate representative QB/RB/WR/TE props and opponent context in the deployed app.
