# PX-200 Trip Detection Troubleshooting

## Summary
PX-200 devices infer trips from a combination of ignition state, motion, and GPS quality.

## Common Reasons Trips Are Not Reported
1. Ignition input is unstable or wired incorrectly.
2. Firmware is below `4.2.0`, which can undercount short trips after long idle periods.
3. GPS fix is delayed or missing at trip start.
4. Motion is recorded but ignition never transitions to an `on` state.

## Recommended Troubleshooting Order
1. Check for ignition flapping or unstable ignition voltage.
2. Confirm firmware version is `4.2.0` or newer.
3. Verify the device obtains GPS lock within 90 seconds of ignition-on.
4. Compare motion and ignition timelines.
5. If all checks pass, inspect installation quality and power integrity.

## Notes
- Repeated ignition anomalies often correlate with missing or split trips.
- On PX-200, unstable ignition is a more common cause of missing trips than total GPS loss.
