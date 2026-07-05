# Anti-UAV System — MVP Specification

*Living document. Updated as each phase is built and decisions are made.*

---

## Overview

Real-time detection, tracking, and ballistic interception of UAV swarms in a Gazebo/ROS2 simulation. A single operator sees a tactical HUD showing radar, turret camera feed, and a telemetry table — the system identifies threats and computes firing solutions automatically.

**Timeline:** 4 weeks solo  
**Language:** Python (core) + React or PyQt5 (HUD)  
**Stack:** ROS2 Humble · Gazebo · ArduPilot SITL · YOLOv8 · NumPy/SciPy · OpenCV

---

## Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  Gazebo Simulation                                                  │
│   ArduPilot SITL ×6–12 ──► drone positions (ground truth)          │
│   Camera plugin        ──► /camera/image_raw  (640×480 @ 30fps)    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ ROS topics
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Detection Node  (yolo_node.py)                                      │
│   YOLOv8 inference per frame → bounding boxes + confidence          │
│   Publishes: /detections  [Detection[]]                              │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Tracker Node  (tracker_node.py)                                     │
│   Hungarian algorithm → frame-to-frame association                  │
│   Kalman filter per track → smooth position + velocity estimate     │
│   Publishes: /tracks  [Track[]]  (ID, pos3d, vel3d, covariance)     │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Ballistics Node  (ballistics_node.py)                               │
│   solver/ballistics.py per track → bearing, elevation, intercept    │
│   Threat scoring + ranking                                           │
│   Publishes: /ballistics  [BallisticSolution[]]                     │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  HUD Frontend  (hud/)                                                │
│   Consumes JSON over WebSocket (rosbridge_server)                   │
│   Renders: top-down radar · turret cam overlay · telemetry table    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Coordinate Convention

- **Frame:** ROS REP-103 — x = north, y = west (left), z = up
- **Origin:** turret base
- **Bearing:** degrees clockwise from north  
  `bearing = atan2(-y, x) mod 360`
- **Elevation:** degrees above horizon  
  `elevation = atan2(z, sqrt(x²+y²))`
- **All distances:** metres

---

## Data Schemas

### Detection (per frame)
```python
{
  "frame_id": int,
  "bbox": [x1, y1, x2, y2],   # pixels
  "confidence": float,
  "centroid_px": [cx, cy]
}
```

### Track (per drone, per frame)
```python
{
  "track_id": int,
  "pos": [x, y, z],            # metres, turret-relative
  "vel": [vx, vy, vz],         # m/s
  "covariance": [[...] × 6],   # 6×6 Kalman P matrix
  "age": int,                  # frames since first detection
  "missed": int,               # consecutive missed frames
  "status": "tracking" | "coasting" | "lost"
}
```

### BallisticSolution (per track, per frame)
```python
{
  "track_id": int,
  "bearing_deg": float,
  "elevation_deg": float,
  "range_m": float,
  "aim_point": [x, y, z],
  "time_to_impact": float | None,
  "threat_score": float,
  "lock_status": "tracking" | "locked" | "lost"
}
```

---

## Phase 1 — Simulation Environment (Week 1)

### Gazebo World
- Flat terrain, 5km × 5km airspace
- Turret at origin with fixed camera mount (640×480, 60° FoV, 30fps)
- Sky backdrop, ambient lighting

### Drone Swarm
- 6–12 ArduPilot SITL instances (configurable via `config/sim.yaml`)
- Flight patterns (each drone picks one randomly at spawn):
  - Sine-wave altitude (±20m, 0.1Hz)
  - Circular loiter (radius 200–800m)
  - Coordinated drift (fixed heading, slow yaw)
  - Evasive weave (S-curve in x-y plane)
- Velocity constraints: max 30 m/s, max accel 5 m/s²
- Spawn range: 500m–2000m from turret

### Launch
```bash
ros2 launch anti_uav_system sim.launch.py swarm_size:=8
```

### Config (`config/sim.yaml`)
```yaml
swarm:
  count: 8
  spawn_range_m: [500, 2000]
  max_speed_ms: 30
camera:
  width: 640
  height: 480
  fov_deg: 60
  fps: 30
```

---

## Phase 2 — Detection & Tracking Pipeline (Week 2)

### Detection Node
- Subscribes to `/camera/image_raw`
- YOLOv8-nano inference (pre-trained COCO, fine-tune on drone imagery if time allows)
- Filter: confidence ≥ 0.5, bbox area 100–50000px²
- Publishes centroids as `Detection[]` on `/detections`

### Tracker Node
- Hungarian assignment: cost = centroid distance (px), max cost = 150px
- Track lifecycle: `tentative` (1 frame) → `tracking` → `coasting` (≤5 missed frames) → `lost` (dropped)
- Kalman state vector: `[x, y, z, vx, vy, vz]`
- Process noise tuned for max drone accel of 5 m/s²
- Publishes `Track[]` on `/tracks`

### Trajectory Prediction
- Linear extrapolation from Kalman state: `pos(t) = pos + vel × t`
- Prediction horizon: 30–60 frames (1–2s)
- Uncertainty cone: covariance projected forward (for HUD visualisation)

---

## Phase 3 — Ballistics Solver (Week 3)

### Intercept Geometry  
*Implemented in `solver/ballistics.py`*

For each track:
1. `r = drone_pos - turret_pos`
2. Solve quadratic for time-to-intercept `t`:  
   `t²(|v|² − V²) + 2t(r·v) + |r|² = 0`  
   where `v` = drone velocity, `V` = muzzle velocity (1000 m/s default)
3. Aim point: `drone_pos + drone_vel × t`
4. Bearing + elevation from aim point direction

### Threat Scoring
```
score = (speed / range) × (1 / (1 + bearing_rate))
```
- Closest + fastest + stable bearing = highest priority
- `bearing_rate`: degrees/second change in bearing (from track history)

### Config (`config/ballistics.yaml`)
```yaml
muzzle_velocity_ms: 1000
max_range_m: 3000
min_confidence: 0.6
threat:
  weights:
    range: 1.0
    speed: 1.0
    bearing_stability: 1.0
```

### Lock Status
- `tracking` — track exists, computing solution each frame
- `locked` — threat score in top-2 AND time_to_impact valid for ≥10 consecutive frames
- `lost` — track dropped

---

## Phase 4 — Tactical HUD (Week 3–4)

### Layout
```
┌─────────────────────────────────────────────────┐
│  TOP-DOWN RADAR (2D)        │  TURRET CAM FEED   │
│  ─────────────────────────  │  ────────────────  │
│  • Range rings (500m, 1km,  │  • YOLOv8 bboxes   │
│    1.5km, 2km)              │  • Track ID labels  │
│  • Drone blip per track     │  • Velocity arrows  │
│  • Velocity vectors         │  • Crosshairs       │
│  • Predicted paths (dashed) │  • LOCKED indicator │
│  • Colour: green→yellow→red │                     │
│    by threat score          │                     │
├─────────────────────────────────────────────────┤
│  TELEMETRY TABLE (sortable by any column)       │
│  ID | Range  | Bearing | Elev | Speed | Status  │
│  01 | 1450m  | 045°    | 12°  | 18m/s | LOCKED  │
│  02 | 1680m  | 078°    | 08°  | 22m/s | TRACKING│
│  03 |  920m  | 120°    | 18°  | 15m/s | LOCKED  │
└─────────────────────────────────────────────────┘
```

### Frontend
- Framework: **React + Electron** (preferred) or PyQt5
- Dark theme, neon accents, monospace font (Roboto Mono or JetBrains Mono)
- Update loop: 30fps, driven by WebSocket messages
- Radar: HTML5 Canvas (React) or QPainter (PyQt5)
- Camera feed: MJPEG stream from `web_video_server` ROS package

### Data transport
```
ROS2 → rosbridge_server → WebSocket (ws://localhost:9090) → HUD
```
Message format: JSON, one message per topic per frame.

---

## Phase 5 — Polish & Output (Week 4)

- RViz config showing 3D swarm + predicted trajectories + firing solutions
- Annotated video: tactical HUD recorded to disk (`annotated_output.mp4`)
- Live demo: turret POV, 8-drone swarm, system locking and tracking in real time

---

## Launch

```bash
# Full system (sim + pipeline + HUD)
ros2 launch anti_uav_system main.launch.py

# Solver only (no ROS, for testing)
python solver/ballistics.py
python solver/kalman.py
python solver/tracker.py
```

---

## Success Criteria

| Criterion | Target |
|-----------|--------|
| Simultaneous tracks | 6–12 UAVs |
| Update rate | 30fps |
| Ballistic solution latency | ≤50ms |
| Track ID consistency | Through ≥5 consecutive missed frames |
| Bearing prediction error | ±5° under nominal conditions |
| HUD frame lag | ≤1 frame (33ms) |

---

## Build Status

| Module | File | Status |
|--------|------|--------|
| Ballistics solver | `solver/ballistics.py` | ✅ Done |
| Kalman filter | `solver/kalman.py` | ✅ Done |
| Tracker | `solver/tracker.py` | ✅ Done |
| ROS2 package scaffold | `package.xml`, `setup.py`, `config/` | ✅ Done |
| Launch file | `launch/main.launch.py` | ✅ Done |
| Detection node | `anti_uav_system/nodes/yolo_node.py` | ⬜ Next |
| Tracker node | `anti_uav_system/nodes/tracker_node.py` | ⬜ Pending |
| Ballistics node | `anti_uav_system/nodes/ballistics_node.py` | ⬜ Pending |
| Gazebo world | `sim/worlds/airspace.world` | ⬜ Pending |
| Turret model | `sim/models/turret/` | ⬜ Pending |
| HUD frontend | `hud/` | ⬜ Pending |

## HUD Reference Notes
From `dashboard inspo.webp`:
- Satellite map base layer on radar (not just rings)
- Green sector cone showing camera/weapon FoV
- Named track icons (not just dots) — colour-coded red=locked, blue=tracking
- Bottom-right lock panel: speed, alt, distance, bearing + weapon APPROVE buttons
- Telemetry table columns: ID, type, time detected, sensor, coords, distance, heading, actions
- Action buttons per row: LOCK ON / RELEASE
