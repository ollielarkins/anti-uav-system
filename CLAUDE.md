# Anti-UAV System — Claude Reference

## What this is
Simulated anti-drone defense system. Detects, tracks, and computes ballistic intercepts for UAV swarms in a Gazebo/ROS2 simulation. 4-week solo MVP.

## Tech stack
- **Simulation:** ROS2 Humble · Gazebo · ArduPilot SITL
- **Detection:** YOLOv8 (`ultralytics`) · OpenCV
- **Tracking:** Hungarian algorithm · Kalman filter (scipy/numpy)
- **Solver:** Python (pure math, no ROS deps)
- **HUD:** React (Electron) or PyQt5 — TBD
- **Comms:** ROS topics / rosbridge WebSocket → frontend

## Directory layout (evolving)
```
anti_uav_system/        # ROS2 package
  nodes/                # ROS node scripts
  launch/               # launch files
  config/               # yaml params (swarm size, camera, ballistics)
solver/                 # pure Python, no ROS deps
  ballistics.py         # intercept geometry & threat scoring
  kalman.py             # Kalman filter per track
  tracker.py            # Hungarian association + track management
sim/
  worlds/               # Gazebo world files
  models/               # turret + drone URDF/SDF
hud/                    # frontend (React or PyQt5)
```

## Coordinate convention
- ROS REP-103: x=forward (north), y=left, z=up
- Bearing: degrees clockwise from north (atan2 in x-y plane, adjusted)
- Elevation: degrees above horizon
- All positions in metres relative to turret origin unless noted

## Key design decisions
- Ballistics solver is standalone Python (no ROS) — testable without simulation
- Kalman filter per track, not a joint state estimator — simpler, scales to 12 UAVs fine
- Hungarian algorithm for frame-to-frame association (scipy.optimize.linear_sum_assignment)
- Intercept solved analytically (quadratic), not iteratively
- Frontend consumes JSON over WebSocket (rosbridge) — decouples HUD from ROS

## Ballistics model
- Muzzle velocity: 1000 m/s (configurable in config/ballistics.yaml)
- Drag: ignored for now (drone ranges <2km, high-velocity round)
- Intercept: solve quadratic `t²(|v|²-V²) + 2t(r·v) + |r|² = 0` for time-to-intercept
  where r = drone_pos - turret_pos, v = drone_vel, V = muzzle_velocity
- Threat score: `1/(range) * speed * bearing_stability` — higher = more urgent

## ROS topics (planned)
| Topic | Type | Publisher |
|-------|------|-----------|
| `/camera/image_raw` | `sensor_msgs/Image` | Gazebo camera plugin |
| `/detections` | custom `Detection[]` | yolo_node |
| `/tracks` | custom `Track[]` | tracker_node |
| `/ballistics` | custom `BallisticSolution[]` | ballistics_node |

## Performance targets
- Track 6–12 UAVs @ 30fps
- Ballistic solutions ≤50ms latency
- Prediction accuracy ±5° bearing under nominal conditions
- Track ID consistency through occlusions

## What's built
- [x] README
- [x] `solver/ballistics.py` — intercept geometry + threat scoring → `docs/ballistics.md`
- [x] `solver/kalman.py` — CV Kalman filter per track → `docs/kalman.md`
- [x] `solver/tracker.py` — Hungarian association + track lifecycle → `docs/tracker.md`

## What's next
- [ ] ROS2 package scaffolding (`anti_uav_system/`)
- [ ] Gazebo world + turret model (`sim/`)
- [ ] YOLOv8 detection node
- [ ] Thin ROS wrapper nodes for tracker + ballistics
- [ ] HUD frontend skeleton

## solver/ is feature-complete (no ROS deps)
Run `python -m solver.ballistics`, `python -m solver.kalman`, `python -m solver.tracker` to verify all passing.
