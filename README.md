# Anti-UAV System

Simulated anti-drone defense system: detect, track, and compute ballistic intercepts for UAV swarms in real-time.

**Stack:** ROS2 · Gazebo · ArduPilot SITL · YOLOv8 · Python · React (or PyQt5)

---

## Architecture

```
Gazebo Sim ──► Camera Feed (ROS topic)
                    │
                    ▼
              YOLOv8 Detector
                    │
                    ▼
          Tracker (Hungarian + Kalman)
                    │
                    ▼
         Ballistics Solver (intercept geometry)
                    │
                    ▼
          Tactical HUD (radar + cam + telemetry)
```

---

## Phases

| Phase | Scope | Week |
|-------|-------|------|
| 1 | Simulation environment — Gazebo world, turret model, 6–12 ArduPilot UAVs | 1 |
| 2 | Detection & tracking — YOLOv8 inference, Hungarian association, Kalman filter, trajectory prediction | 2 |
| 3 | Ballistics solver — bearing/elevation/range, intercept point, threat prioritisation | 3 |
| 4 | Tactical HUD — top-down radar, turret cam overlay, telemetry table, 30fps update loop | 3–4 |
| 5 | Polish — RViz overlays, annotated video output, docs | 4 |

---

## HUD Layout

```
┌─────────────────────────────────────────────────┐
│  TOP-DOWN RADAR              │  TURRET CAM FEED  │
│  • Range rings (500m, 1km)   │  • YOLOv8 bboxes  │
│  • Drone blips + vectors     │  • Track ID labels │
│  • Predicted paths (dashed)  │  • Crosshairs/lock │
├──────────────────────────────────────────────────┤
│  ID | Range  | Bearing | Elev | Speed | Status   │
│  01 | 1450m  | 045°    | 12°  | 18m/s | LOCKED   │
│  02 | 1680m  | 078°    | 08°  | 22m/s | TRACKING │
└──────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# Launch full system
ros2 launch anti_uav_system main.launch.py
```

Config lives in `config/` — swarm size, camera params, ballistics model.

---

## Success Criteria

- Track 6–12 UAVs simultaneously at 30fps
- Maintain track ID consistency across occlusions
- Ballistic solutions computed within 50ms
- Prediction accuracy within ±5° bearing error

---

## Dependencies

- ROS2 (Humble)
- Gazebo
- ArduPilot SITL
- YOLOv8 (`ultralytics`)
- OpenCV
- Python 3.10+
- React / PyQt5 (HUD frontend)
