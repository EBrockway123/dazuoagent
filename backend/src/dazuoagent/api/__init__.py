"""HTTP layer.

`api/v1/router.py` aggregates the versioned routers. New endpoints should be
added as a new module under `api/v1/` and registered in that aggregator — do
not import routers directly from `main.py`.
"""