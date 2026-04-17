# Current Device Error Codes

Effective date: 2026-01-15
Authority: Fleet Platform Support

## Codes
- `E104`: Ignition voltage unstable during trip detection window.
- `E201`: Battery voltage below operational threshold.
- `E315`: Temperature probe reading out of expected range.
- `E412`: GPS lock not acquired within expected startup window.

## Interpretation Guidance
- `E104` frequently appears alongside missing trips, trip fragmentation, or false idle inflation.
- `E201` should be correlated with battery voltage readings and engine-off timing.
- `E412` can contribute to missing trip starts, but is less common than ignition instability on PX-200 devices.
