# Tracker

**File:** `solver/tracker.py`  
**Deps:** `numpy`, `scipy` (Hungarian assignment), `solver.kalman`, `solver.ballistics`  
**Self-test:** `python -m solver.tracker`

---

## What it does

Manages a pool of `KalmanTrack` instances across frames. Takes a list of 3D position measurements each frame and returns a ranked list of ballistic solutions — one per confirmed drone.

Responsibilities:
1. **Association** — assign each new detection to an existing track (or spawn a new one)
2. **State estimation** — run predict/update on each track's Kalman filter
3. **Lifecycle management** — promote tentative tracks, coast through occlusions, drop lost tracks
4. **Output** — emit full `BallisticSolution` dicts ranked by threat score

---

## Track lifecycle

```
tentative ──(hits >= 3)──► tracking ──(missed > 0)──► coasting ──(missed > 5)──► [dropped]
    ▲                          │
    └──── new detection        └──── (detection resumes) ──► tracking
```

| Status | Meaning |
|--------|---------|
| `tentative` | Fewer than 3 consecutive hits — not yet emitted to output |
| `tracking` | Confirmed, detection arriving normally |
| `coasting` | Missed detection this frame, predicting forward via Kalman |
| `lost` | Dropped after `MAX_COAST_FRAMES` (5) consecutive misses |

Only `tracking` and `coasting` tracks are included in output.

---

## Association algorithm

**Hungarian assignment** via `scipy.optimize.linear_sum_assignment`.

Cost matrix: Euclidean distance (metres) between each predicted track position and each new detection.

Pairs with cost > `MAX_ASSOCIATION_DIST` (100m) are treated as unmatched — prevents associating a new detection with a distant stale track.

```
predicted positions (n_tracks × 3)
         ×
detections (n_dets × 3)
         ↓
cost matrix (n_tracks × n_dets) of distances
         ↓
linear_sum_assignment → optimal (track, detection) pairs
         ↓
filter out pairs where dist > 100m
```

---

## API

### `Tracker(turret_pos=np.zeros(3), muzzle_vel=1000.0)`
Initialise tracker. `turret_pos` sets the origin for all ballistic calculations.

---

### `.update(detections, dt=1/30) → list[dict]`
Main entry point. Call once per frame.

| Param | Type | Description |
|-------|------|-------------|
| `detections` | `list[np.ndarray]` | 3D positions (metres), one per detection this frame |
| `dt` | `float` | Time since last frame (seconds) |

Returns a list of track dicts (see schema below), **sorted by threat score descending** (highest threat first). Only confirmed + coasting tracks included.

---

### `.active_count → int`
Number of non-tentative tracks.

---

## Output dict schema (per track)
```python
{
  # From ballistics solver
  "bearing_deg":    float,
  "elevation_deg":  float,
  "range_m":        float,
  "aim_point":      [x, y, z],
  "time_to_impact": float | None,
  "threat_score":   float,

  # Track metadata
  "track_id":  int,
  "status":    "tracking" | "coasting",
  "age":       int,          # total frames this track has existed
  "pos":       [x, y, z],   # current Kalman position estimate
  "vel":       [vx, vy, vz],
  "covariance": [[...] × 6]  # 6×6 Kalman P matrix
}
```

---

## Configuration
These are module-level constants — move to `config/tracker.yaml` when wiring into ROS:

| Constant | Default | Meaning |
|----------|---------|---------|
| `MAX_ASSOCIATION_DIST` | 100 m | Beyond this, detection won't be matched to existing track |
| `CONFIRM_HITS` | 3 frames | Hits required before track is promoted to `tracking` |
| `MAX_COAST_FRAMES` | 5 frames | Missed frames before track is dropped (~167ms @ 30fps) |

---

## Known simplifications
- **3D measurement only** — expects position in metres. The ROS detection node is responsible for projecting 2D pixel detections to 3D (using depth or Gazebo ground truth).
- **Euclidean distance cost** — works well at 30fps with drones moving <30 m/s (max 1m between frames). If frame rate drops, consider velocity-gated Mahalanobis distance.
- **No re-ID after drop** — a track dropped after 5 missed frames gets a new ID if re-detected. Fine for the MVP; add appearance features if persistent IDs matter.
