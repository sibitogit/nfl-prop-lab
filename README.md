# NFL Prop Lab — Candidate v0.7

Reliability-focused build.

## Changes
- Uses nflverse CSV weekly player stats instead of Parquet.
- Removes the pyarrow dependency.
- Moves statistical calculations into `core.py`.
- Adds unit-test cases for Over/Under, pushes, hit-rate denominator, line explorer, consistency, and defense-vs-position aggregation.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Test
```bash
python -m pytest tests
```

The build environment cannot perform a full online Streamlit boot because outbound package installation is blocked, so the statistical core is intentionally testable independently of Streamlit/network access.
