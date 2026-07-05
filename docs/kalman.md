# Kalman Filter

**File:** `solver/kalman.py`  
**Deps:** `numpy` only  
**Self-test:** `python -m solver.kalman`

---

## What it does

Single-target state estimator. Takes noisy 3D position measurements and produces smooth position + velocity estimates with associated uncertainty (covariance).

Used by `solver/tracker.py` — one `KalmanTrack` instance per active drone.

---

## Model

**Constant-velocity (CV) model** — assumes drones fly smooth paths with small, unmodelled accelerations.

State vector (6D):
```
x = [x, y, z, vx, vy, vz]
```

### State transition (predict step)
```
x_k = F·x_{k-1}
P_k = F·P_{k-1}·Fᵀ + Q

F = [[1, 0, 0, dt, 0,  0 ],
     [0, 1, 0, 0,  dt, 0 ],
     [0, 0, 1, 0,  0,  dt],
     [0, 0, 0, 1,  0,  0 ],
     [0, 0, 0, 0,  1,  0 ],
     [0, 0, 0, 0,  0,  1 ]]
```

### Measurement update
```
H = [[1, 0, 0, 0, 0, 0],   # observe position only
     [0, 1, 0, 0, 0, 0],
     [0, 0, 1, 0, 0, 0]]

S = H·P·Hᵀ + R
K = P·Hᵀ·S⁻¹
x = x + K·(z - H·x)
P = (I - K·H)·P
```

### Noise parameters
| Parameter | Value | Meaning |
|-----------|-------|---------|
| `SIGMA_A` | 5.0 m/s² | Max unmodelled drone acceleration |
| `SIGMA_R` | 5.0 m | Position measurement noise (1σ) |

Process noise `Q` uses the **discrete white-noise acceleration model** — each axis independently gets a 2×2 block:
```
q_axis = sigma_a² × [[dt⁴/4, dt³/2],
                      [dt³/2, dt²  ]]
```
This is the standard form for CV Kalman trackers.

---

## API

### `KalmanTrack(pos, vel=None)`
Initialise a new track at position `pos` (shape (3,)). Initial velocity defaults to zero; supply `vel` if you have a prior estimate.

Initial covariance `P = 100·I` (loose — tightens quickly after a few updates).

---

### `.predict(dt=1/30) → np.ndarray`
Advance the state forward by `dt` seconds. Returns predicted position (3,).  
Call once per frame before `update()`.

---

### `.update(measurement) → np.ndarray`
Fuse a new 3D position measurement (shape (3,)). Returns corrected position (3,).

---

### `.pos → np.ndarray`
Current position estimate (3,).

### `.vel → np.ndarray`
Current velocity estimate (3,).

### `.covariance → np.ndarray`
Full 6×6 covariance matrix `P`. Diagonal entries `P[0,0]`, `P[1,1]`, `P[2,2]` give position variance per axis. Used by HUD to draw uncertainty cones.

---

## Performance (self-test)
Drone flying 500m-radius circle at ~52 m/s, SIGMA_R=5m noise, 90 frames (3s @ 30fps):

| Metric | Value |
|--------|-------|
| Raw measurement error | ~7.3m |
| Filtered position error | ~3.3m |
| Velocity error at 3s | ~7 m/s (~13% of true speed) |

Velocity estimates converge within ~2–3s of track initialisation.

---

## Known simplifications
- **Constant-velocity only** — no manoeuvre detection. Evasive drones will cause the filter to lag momentarily. Upgrade path: IMM (Interacting Multiple Model) filter if evasive tracking becomes a requirement.
- **Independent axes** — Q is block-diagonal. Correlated manoeuvres (e.g. banked turns coupling x and y) are not modelled.
- **Fixed SIGMA_R** — measurement noise is homogeneous. In a real system it would vary with range and detection confidence.
