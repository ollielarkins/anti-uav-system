# HUD Specification — Anti-UAV Tactical Dashboard

Design spec for `hud/`. Same visual language as the reference dashboard — satellite map base, dense telemetry, split-view — adapted to the anti-UAV tracking and ballistics system.

See `docs/hud-reference-analysis.md` for the full reference decomposition.

---

## Global Layout

```
┌─────────────────────────────────────────────────────────┐  32px
│  TOP BAR                                                │
├──────────────────────────────────┬──────────────────────┤  ~360px
│  RADAR MAP  (~68% width)         │  TURRET CAM FEED     │
│                                  │  (~32% width)        │
├──────────────────────────────────┬──────────────────────┤  ~140px
│  TELEMETRY TABLE  (~68% width)   │  BALLISTIC DETAIL    │
│                                  │  (~32% width)        │
└──────────────────────────────────┴──────────────────────┘
```

Same 68/32 split held consistently. All four zones always visible — no default-collapsed panels.

---

## Colour Palette

Adapted from the reference — darker, more neon, higher contrast befitting a simulated engagement system.

| Token | Hex | Used for |
|-------|-----|----------|
| `bg-base` | `#0d0f1a` | App background, top bar, table |
| `bg-raised` | `#161929` | Panel headers, selected rows |
| `bg-card` | `#1e2235` | Detail cards |
| `border` | `#2a2e45` | Row dividers, panel separators |
| `text-primary` | `#e4e8f0` | Main labels, data values |
| `text-secondary` | `#7a80a0` | Column headers, sub-labels |
| `text-mono` | `#b0b8d0` | Coordinates, ranges, bearings |
| `accent-threat` | `#ff3030` | LOCKED drone icon, bbox, tag |
| `accent-track` | `#00c8ff` | TRACKING drone icons, labels |
| `accent-coast` | `#f0a020` | COASTING (missed frames) icons |
| `accent-cone` | `#00ff88` (25% opacity) | Camera FoV cone fill |
| `accent-cone-border` | `#00ff88` (70% opacity) | Cone boundary lines |
| `accent-ring` | `#ffffff` (25% opacity) | Range rings |
| `accent-vector` | `#ffffff` (60% opacity) | Velocity vectors, predicted paths |
| `accent-intercept` | `#ff8800` | Intercept aim-point marker |
| `btn-lock` | `#00c8ff` | LOCK ON border + text |
| `btn-release` | `#8040c0` | RELEASE fill |
| `btn-fire` | `#ff6000` | FIRE SOLUTION fill |
| `panel-live` | `#ff2222` | LIVE indicator dot |

---

## Zone 1 — Top Bar

32px, `bg-base`, full width. Sparse — only what the operator needs at a glance.

### Left
- **App icon** — anti-UAV target reticle logo
- **"ANTI-UAV SIM"** label — white, 13px medium
- **Swarm size indicator** — e.g. "8 UAV" — pill badge, `accent-track` border

### Centre
- **Mission clock** — `HH:MM:SS`, large white monospace, live-updating
- **Frame counter** — "FPS: 30" small grey — confirms pipeline is live

### Right
- **Track counts** — three pills:
  - `TRACKING: N` — `accent-track` text
  - `COASTING: N` — `accent-coast` text
  - `LOCKED: N` — `accent-threat` text
- **ROS status dot** — green (connected) / red (disconnected) + "ROS" label
- **"SIMULATION"** badge — distinguishes sim from live deployment

---

## Zone 2a — Radar Map Panel

### Base layer
Gazebo world projected top-down. Two options (config-switchable):
1. **Satellite tile** — real satellite imagery if lat/lon is configured (OpenStreetMap tile layer)
2. **Synthetic terrain** — Gazebo ground texture rendered to canvas (fallback when no geo-ref)

Either way the map pans with the swarm centre of mass to keep all tracks on screen.

### Range rings
Same as reference: concentric dashed circles from turret origin.
- Rings: **500m, 1km, 1.5km, 2km**
- Style: `1px dashed`, `accent-ring`
- Labels: small `text-secondary` on ring, top position

### Camera FoV Cone
- **Green filled sector** from turret origin showing current camera bearing ± FoV/2
- Fill: `accent-cone`; border: `accent-cone-border`
- Rotates in real-time as turret azimuth updates
- Angle width = configured camera FoV (default 60°)
- Radius = `max_range_m` from config (default 2km)

### Turret Icon
- Fixed at canvas centre
- Crosshair-in-circle icon, white, 20px
- No label

### Drone Icons — Tracking
Per confirmed track (`status: "tracking"`):
- **Top-down drone silhouette**, 16px, `accent-track`
- **Name label pill** above: "UAV-{id}" — dark rounded pill, `text-primary`, 11px
- **Velocity vector arrow**: line from icon in heading direction, length = speed × scale, `accent-vector`, 60% opacity
- **Predicted path**: dashed line extending 2s ahead along Kalman-predicted trajectory, same colour, 30% opacity
- **Uncertainty ellipse** (optional, on hover): covariance projected to x-y plane, thin dashed outline

### Drone Icons — Coasting
Track missed frames but not yet lost:
- Same icon, recoloured `accent-coast` (amber)
- Dashed outline on label pill

### Drone Icons — Locked
Highest-threat confirmed track:
- Icon size: 24px, `accent-threat`
- Label pill: red fill, white text, "UAV-{id}"
- **Intercept marker**: small `accent-intercept` cross/circle at predicted aim point
- **Engagement line**: thin dashed line from turret to aim point, `accent-intercept`, 50% opacity

### Toolbar — Left vertical strip
30px wide, `bg-raised`:
- Pan/select cursor
- Zoom in/out (+/-)
- Toggle range rings
- Toggle velocity vectors
- Toggle predicted paths
- Toggle uncertainty ellipses

### Toolbar — Bottom horizontal strip
`bg-raised`, 28px tall:
- Left: **AUTO / MANUAL** toggle (auto-selects highest-threat target vs operator picks)
- Centre: map mode (satellite / synthetic / wireframe)
- Right: zoom reset, centre-on-swarm

---

## Zone 2b — Turret Camera Feed

### Header
- `bg-raised`, 24px
- Left: **"TURRET CAM"** label — white, 12px medium
- Live indicator: **red dot + "LIVE"** when streaming, grey + "OFFLINE" when not
- Right: brightness/contrast icon

### Feed
- Full panel below header
- **Raw camera image** at 640×480, scaled to fill panel, `object-fit: cover`
- Overlays (rendered on a Canvas element above the image):
  - **Bounding boxes**: `accent-threat` for locked, `accent-track` for tracked — 2px rect
  - **Track ID label**: dark pill above each bbox, "UAV-{id}" with drone icon, 11px
  - **Velocity arrow**: small arrow inside or beside bbox showing estimated velocity direction
  - **Crosshair**: thin + static cross centred on locked target bbox, `accent-threat`
  - **Lock ring**: animated pulsing circle around locked target bbox

### No overlays on undetected frames — blank feed shows "NO SIGNAL" centred.

---

## Zone 3a — Telemetry Table

### Column headers
Small, uppercase, `text-secondary`, 11px, `letter-spacing: 0.06em`:

`ID` | `STATUS` | `RANGE` | `BEARING` | `ELEV` | `SPEED` | `T-IMPACT` | `THREAT` | `ACTIONS`

### Rows — one per confirmed + coasting track
Height: 28px. Sorted by threat score descending (highest threat top). Sortable by any column header click.

| Column | Format | Example |
|--------|--------|---------|
| `ID` | `UAV-NN`, bold mono | `UAV-03` |
| `STATUS` | coloured pill | `LOCKED`, `TRACKING`, `COASTING` |
| `RANGE` | `NNNNm`, mono | `1450m` |
| `BEARING` | `NNN.N°`, mono | `045.2°` |
| `ELEV` | `±NN.N°`, mono | `+12.4°` |
| `SPEED` | `NN.Nm/s`, mono | `18.3m/s` |
| `T-IMPACT` | `N.NNs`, mono | `1.45s` |
| `THREAT` | `N.NNNNN` | `0.01240` |
| `ACTIONS` | buttons | see below |

Status pill colours:
- `LOCKED` — `accent-threat` fill, white text
- `TRACKING` — `accent-track` outline, `accent-track` text
- `COASTING` — `accent-coast` outline, `accent-coast` text

### Action buttons

**LOCK ON** — not yet locked:
- Outlined pill, `btn-lock` border + text, transparent bg
- Clicking sets this track as the PRIMARY target (updates cam feed, detail panel)

**RELEASE** — currently locked:
- Filled pill, `btn-release`, white text
- Clears lock; system returns to AUTO selection if AUTO mode is on

**No FIRE button in the table** — firing decision lives only in the Ballistic Detail panel (two-step safety, same as reference).

Secondary icon buttons per row (after main action):
- **Pin** — keep track visible even if it drops out of threat ranking
- **Centre map** — pan radar to this track

---

## Zone 3b — Ballistic Detail Panel

Shown for the currently LOCKED track. Falls back to "Select a target" placeholder when nothing locked.

### Header
- `bg-raised`, 28px
- Left: `accent-threat` rounded tag "UAV-{id}" + target description "ATTACK DRONE", white medium
- Right: age counter "T+{frames} frames" in `text-secondary`

### Stats row
Single line, `text-secondary`, 11px, icon before each value:
`↗ {bearing}°` | `↕ {elevation}°` | `◎ {range}m` | `⚡ {speed}m/s` | `⏱ ToF: {t}s`

### Body — two columns

**Left (~45%):** turret camera thumbnail
- Live crop of the locked target from the camera feed
- **Red crosshair reticle** overlaid, `accent-threat`, thin lines with centre gap
- **Aim point dot** at computed intercept, `accent-intercept` — shows where the round should exit the barrel, slightly offset from drone centre when leading

**Right (~55%):** ballistic solution breakdown
Three info rows + one action:

```
Azimuth:    045.2°      ← rounded bearing to aim point
Elevation:  +12.4°      ← pitch angle
Aim offset: +1.15°      ← delta from current drone bearing (lead angle)
T-impact:   1.45s       ← time of flight
```
Values: monospace, `text-mono`, 12px

Below the values:
- **[FIRE SOLUTION]** full-width button
  - Background: `btn-fire`
  - White bold uppercase text
  - This is the APPROVE equivalent — second step after LOCK ON

### Footer
- **[CLEAR LOCK]** full-width button, muted, `bg-card`, `text-secondary`
- Separator above

---

## Typography

Same rules as reference — Inter/Roboto for labels, monospace for all numbers:

| Use | Font | Size | Weight |
|-----|------|------|--------|
| Telemetry numbers | `JetBrains Mono` or `Roboto Mono` | 12px | Regular |
| Column headers | `Inter`, uppercase | 11px | Regular, +letter-spacing |
| Map track labels | `Inter` | 11px | Regular |
| Status pills | `Inter`, uppercase | 10px | Bold |
| Button text | `Inter`, uppercase | 11px | Bold |
| ID column | `JetBrains Mono` | 12px | Bold |
| Stats row | `Inter` | 11px | Regular |
| Top bar mission label | `Inter` | 13px | Medium |
| Clock | `JetBrains Mono` | 15px | Bold |

---

## Interaction Model

1. Drones detected → appear as blue blips on radar + rows in telemetry table
2. Operator clicks **LOCK ON** (or AUTO mode auto-selects highest threat)
3. **Camera feed** switches to turret-cam stream; bounding box + crosshair appear on locked drone
4. **Ballistic Detail panel** populates with aim solution
5. Operator reviews bearing / elevation / ToF
6. Clicks **FIRE SOLUTION** — sends command to ballistics node / records engagement
7. **RELEASE** at any point returns to tracking state

---

## Data Sources (from ROS)

| HUD element | ROS topic | Update rate |
|-------------|-----------|-------------|
| Drone blips + vectors | `/tracks` | 30fps |
| Bounding boxes | `/detections` | 30fps |
| Ballistic solutions + threat scores | `/ballistics` | 30fps |
| Camera feed | MJPEG via `web_video_server` | 30fps |
| Turret azimuth (cone direction) | `/turret/state` | 30fps |

All topics consumed via **rosbridge WebSocket** (`ws://localhost:9090`), JSON format.

---

## Frontend Stack

- **React + Electron** — desktop app, no browser sandbox restrictions
- **HTML5 Canvas** — radar map, overlays, FoV cone (direct pixel control, no SVG jitter)
- **MJPEG `<img>` tag** — camera feed (zero latency, no WebRTC setup)
- **CSS Grid** — the four-zone layout (two rows, two columns per row)
- Fonts loaded locally: `JetBrains Mono`, `Inter`

---

## Key Design Principles (adapted from reference)

- **Colour = state, always** — blue/amber/red for tracking/coasting/locked, no text-only state
- **Two-step engagement** — LOCK ON → FIRE SOLUTION, never a single click to fire
- **Split view always** — map and camera feed simultaneously visible; radar context + visual confirmation at all times
- **Monospace for numbers** — prevents layout shift as values update at 30fps
- **Threat score drives sort order** — highest threat always top of table without operator intervention
- **Cone shows where the system is looking** — operator can see immediately if a drone is outside FoV
