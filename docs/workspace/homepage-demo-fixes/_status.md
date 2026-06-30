# Homepage Demo Fixes

- Status: verified locally
- Scope: slow demo GIF, prevent GIF text overflow, move hero evidence card up.
- Verification:
  - `python3 -m pytest tests/unit/website/test_launch_website.py -q` -> 17 passed
  - GIF metadata check -> 3 frames at 12000ms each
  - Local browser screenshot -> hero card starts in first-view composition; console clean
