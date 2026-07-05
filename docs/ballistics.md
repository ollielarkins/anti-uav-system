# Ballistics Solver

**File:** `solver/ballistics.py`  
**Deps:** `numpy` only — no ROS, runs standalone  
**Self-test:** `python solver/ballistics.py`

---

## What it does

Given a stationary turret and a drone with known position + velocity, computes:
- Where to aim (bearing, elevation)
- When the projectile hits (time-to-impact)
- How dangerous the drone is (threat score)

---

## Intercept geometry

The intercept problem: find the time `t` at which a projectile fired at muzzle velocity `V` reaches the drone's future position.

**Drone future position:** `P_drone(t) = drone_pos + drone_vel × t`  
**Projectile distance:** `|aim_point - turret_pos| = V × t`

Substituting and expanding into a quadratic in `t`:

```
t²(|v|² − V²) + 2t(r·v) + |r|² = 0
```

where:
- `r = drone_pos − turret_pos` (relative position)
- `v = drone_vel`
- `V = muzzle_velocity` (default 1000 m/s)

Take the smallest positive root. If no positive root exists (drone unreachable), fall back to current position.

---

## API

### `intercept_time(r, v, muzzle_vel) → float | None`
Solves the quadratic and returns the smallest positive time-to-intercept, or `None` if unsolvable.

| Param | Type | Description |
|-------|------|-------------|
| `r` | `np.ndarray` shape (3,) | Relative position (drone − turret), metres |
| `v` | `np.ndarray` shape (3,) | Drone velocity, m/s |
| `muzzle_vel` | `float` | Muzzle velocity, m/s (default 1000) |

---

### `solve(turret_pos, drone_pos, drone_vel, muzzle_vel) → dict`
Full ballistic solution for one drone.

| Param | Type | Description |
|-------|------|-------------|
| `turret_pos` | `np.ndarray` (3,) | Turret position in world frame |
| `drone_pos` | `np.ndarray` (3,) | Drone position |
| `drone_vel` | `np.ndarray` (3,) | Drone velocity |
| `muzzle_vel` | `float` | Default 1000 m/s |

Returns:
```python
{
  "bearing_deg":    float,        # clockwise from north, 0–360
  "elevation_deg":  float,        # degrees above horizon
  "range_m":        float,        # straight-line distance to drone NOW
  "aim_point":      np.ndarray,   # predicted intercept position
  "time_to_impact": float | None  # seconds; None if no solution
}
```

---

### `threat_score(range_m, speed, bearing_rate_deg_s) → float`
Scalar priority score — higher = more urgent.

```
score = (speed / range) × (1 / (1 + bearing_rate))
```

- **Proximity:** closer drones score higher
- **Speed:** faster drones score higher  
- **Bearing stability:** drones on a steady bearing (not jinking) score higher — they're on a collision course

`bearing_rate_deg_s` defaults to 0 if not yet tracked across frames.

---

### `rank_threats(solutions) → list`
Sorts a list of solution dicts (each must have `"threat_score"` key) in-place, highest first. Returns the same list.

---

## Coordinate convention

- **x** = north, **y** = west (left), **z** = up (ROS REP-103)
- **Bearing** = `atan2(-y, x) mod 360` (clockwise from north)
- **Elevation** = `atan2(z, sqrt(x²+y²))`

---

## Known simplifications

- **No drag** — at muzzle velocity 1000 m/s and ranges <2km, drag correction is <0.5%. Add when testing with real-world ballistic tables.
- **Linear drone motion** — intercept assumes constant velocity. Kalman-predicted position should replace raw position as input once the tracker is live.
- **Bearing rate defaults to 0** — until track history is available from the tracker, bearing stability is not factored in.

---

## Example

```python
import numpy as np
from solver.ballistics import solve, threat_score

turret = np.array([0.0, 0.0, 0.0])
drone  = np.array([1000.0, 0.0, 50.0])   # 1km north, 50m alt
vel    = np.array([0.0, -20.0, 0.0])      # moving east at 20 m/s

sol = solve(turret, drone, vel)
# {'bearing_deg': 1.15, 'elevation_deg': 2.86, 'range_m': 1001.2,
#  'aim_point': array([...]), 'time_to_impact': 1.001}

sol["threat_score"] = threat_score(sol["range_m"], 20.0)
```
