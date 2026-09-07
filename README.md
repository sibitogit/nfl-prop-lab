# NFL Prop Lab — Candidate v0.9.2 Beta

Validation/polish build after the first successful Research Summary deployment.

## Improvements
- Position-aware default rushing lines (QB/RB/WR no longer share the same starting point).
- Sample-quality label and explicit game count.
- Research Summary says "historical hits" instead of ambiguous "wins".
- TD/INT Line Explorer keeps nearby lines at sportsbook-style half increments.
- Added a validation matrix covering representative QB/RB/WR/TE props, Over/Under, pushes, consistency metrics, and defense-vs-position aggregation.

## Validation
Automated test suite is expected to cover:
- Over and Under grading
- Push exclusion from hit-rate denominator
- QB passing yards
- RB rushing yards
- WR receptions
- TE receiving yards
- Consistency percentiles
- Defense-vs-position aggregation/ranking
- Research Summary logic

No paid dependency or service was added.
