# Input Pack Notes

## Overview
This input pack contains:
- troubleshooting and support documentation in `docs/`
- structured fleet-style data in `data/`
- a seed list of user questions in `questions_seed.csv`

## Data Files
- `asset_registry.csv`: Asset metadata.
- `daily_asset_metrics.csv`: Daily summary metrics by asset.
- `alert_events.csv`: Alert events and notable operational signals.

## Important Caveats
The pack intentionally includes realistic imperfections.

### Documents
- Not all documents have the same authority.
- One document is explicitly legacy or superseded.
- If documents conflict, we expect you to handle uncertainty sensibly.

### Data
- Some fields are blank when not applicable.
- One asset identifier appears in a legacy format in one event row.
- One alert row is duplicated.
- Not every business conclusion can be proven with the available data; we expect you to acknowledge limits when necessary.

## What We Are Looking For
We are not looking for perfect domain expertise.
We are looking for:
- grounded evidence use
- careful handling of ambiguity
- sensible query and retrieval design
- evaluation rigor
- clear communication

## Suggested Interpretation Rules
You may define your own system behavior, but strong solutions usually:
- prioritize more current sources over legacy ones
- distinguish between supported conclusions and plausible hypotheses
- ask clarifying questions when the request is too broad
- avoid overstating confidence
