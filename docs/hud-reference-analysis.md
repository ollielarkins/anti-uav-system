# HUD Reference Analysis — Drone Guard Dashboard

Full visual decomposition of `dashboard inspo.webp`. Every element, colour, layout decision, and interaction pattern documented.

---

## Global Layout

Three horizontal zones, full-screen, no browser chrome:

```
┌─────────────────────────────────────────────────────────┐  ~30px
│  TOP BAR  (full width)                                  │
├──────────────────────────────────────┬──────────────────┤  ~340px
│  MAP / RADAR PANEL  (~70% width)     │  CAMERA FEED     │
│                                      │  (~30% width)    │
├──────────────────────────────────────┬──────────────────┤  ~130px
│  TELEMETRY TABLE  (~70% width)       │  TARGET DETAIL   │
│                                      │  (~30% width)    │
└──────────────────────────────────────┴──────────────────┘
```

The 70/30 split is consistent across both rows — map and telemetry table share the same left column width as camera feed and target detail share the right.

---

## Colour Palette

| Token | Hex (approx) | Used for |
|-------|-------------|----------|
| `bg-base` | `#1a1c2a` | App background, top bar, table |
| `bg-raised` | `#22253a` | Panel headers, selected rows |
| `bg-card` | `#2a2d42` | Detail cards, button backgrounds |
| `border` | `#32364e` | Row dividers, panel borders |
| `text-primary` | `#e8eaf0` | Main labels, data values |
| `text-secondary` | `#8a8fa8` | Column headers, sub-labels |
| `text-mono` | `#c8cad8` | Coordinates, distances, headings |
| `accent-threat` | `#e03030` | Locked target icon, bbox, tag |
| `accent-track` | `#4ab0e0` | Tracking drone icons, labels |
| `accent-cone` | `#40c060` (30% opacity) | Camera/weapon FoV cone fill |
| `accent-cone-border` | `#40c060` (80% opacity) | Cone boundary lines |
| `accent-ring` | `#ffffff` (35% opacity) | Range rings, dashed |
| `btn-lock` | `#f0a020` | LOCK ON button border + text |
| `btn-release` | `#7b5ea7` | RELEASE button fill |
| `btn-approve` | `#e8920a` | APPROVE! button fill |
| `btn-send` | `#1a6080` | SEND TO EFFECTOR fill |
| `status-live` | `#ff4444` | LIVE indicator dot |

---

## Zone 1 — Top Bar

Full-width strip, `bg-base`, ~30px height. Dense information row, left-to-right:

### Left cluster
- **Gear icon** — settings access, `text-secondary`, 14px
- **Drone Guard logo** — stylised target-circle + drone motif, white
- **"G5" badge** — small pill, green border, green text — system/unit identifier
- **"PAYLOAD" dropdown** — dark button with down-caret, `text-primary` — active mode selector

### Status indicators (centre-left)
- **Two circle icons** — orange and red — system alert states (likely weapons ready / armed)
- **"M" avatar** — blue filled circle with white letter — current operator / unit ID
- **Mission label** "Magen Haaeretz 23/5" — white text, medium weight — operation name + date

### Centre
- **Clock** "15:40" large white + "35" smaller grey — 24h mission clock, seconds as suffix
- **Person icon + "Arrow 2" dropdown** — active operator / platform selector

### Right cluster
- **Stat counters**: three numeric values ("59", "1,204", "305") with small uppercase labels below ("DKG", "RCWS") — engagement/detection counters
- **Network icons** — WiFi, signal strength
- **Eye icon** — observation/surveillance mode toggle
- **"LOCAL" badge** — comms mode indicator

---

## Zone 2a — Map / Radar Panel

### Base layer
Real **satellite imagery** — aerial photography with terrain (fields, roads, buildings) in natural earth tones (greens, greys, beige). This is not a synthetic radar — it is a geospatial map with tactical overlays on top. The map scrolls/pans; "Panorama" text label visible near top indicates the current view name or mode.

### Range rings
Concentric dashed circles centred on the base/turret:
- Labels: **500M, 1,000M, 1,500M, 2,000M, 2,500M**
- Style: `1px dashed`, white at ~35% opacity
- Spacing: uniform 500m increments
- Labels placed on the ring, small sans-serif, `text-secondary`

### Camera / Weapon FoV Sector Cone
- Semi-transparent **green filled triangle** from base pointing NE
- Cone angle: approximately 30–40°
- Fill: `accent-cone` (~30% opacity)
- Two solid boundary lines: `accent-cone-border` (~80% opacity), slightly thicker than ring lines
- Represents active camera or weapon engagement zone
- Extends roughly to 2,500m range

### Base / Turret Icon
- Centre of map (slightly lower-left)
- Circular icon: concentric rings like a radar dish or targeting reticle
- White/light grey
- No label

### Drone Icons — Tracking (blue)
Each tracked drone renders as:
- **Drone silhouette icon** — stylised top-down quadrotor or fixed-wing shape, ~18px
- Colour: `accent-track` (`#4ab0e0`) for confirmed tracks
- **Name label pill** above the icon: dark rounded rectangle (~4px radius), white text, small (~11px), e.g. "Arrow 1", "Stinger", "Hawk"
- **Velocity vector line**: thin white line extending from the icon in the heading direction, length proportional to speed
- Tracks visible: Arrow 1, Chakra, Stinger, Hawk, Reshef 1, Roamer 1, Arrow 2

### Drone Icon — Locked Threat (red)
Track ID 23 renders distinctly:
- **Larger icon** (~28px) — same drone silhouette but red (`accent-threat`)
- **Red number tag** above: dark-red rounded pill with white "23"
- **"-15" delta indicator** below or beside the icon — altitude change or altitude AGL
- Engagement **line** drawn from base to drone — thin white or light line indicating firing solution vector

### Toolbar — Left vertical strip
~30px wide, full panel height, `bg-raised`:
- Icons (top to bottom): cursor/select, person, vehicle, unknown shape, target circle, polygon draw, info
- Active tool highlighted

### Toolbar — Bottom horizontal strip
~30px tall, full panel width, `bg-raised`:
- Left: AUTO/MANUAL toggle pill
- Centre: map tool icons (grid, loop, pencil, settings, layers, refresh)
- Right: zoom-level buttons "3", "2", "1", "Q"

### Resize handle
A `<<` button on the right edge of the map panel, dark background — collapses/expands the camera feed.

---

## Zone 2b — Camera Feed Panel

### Header
- `bg-raised` strip, full panel width, ~24px
- Text: "**Stinger** [LIVE]" — "Stinger" is the camera name, "[LIVE]" suffix in brackets, lighter weight
- Right: yellow sun/brightness icon — exposure or day/night toggle

### Feed
- Full panel width below header
- Background: **light grey/white** — washed sky or fog conditions (not dark)
- **Drone 23** visible as a dark silhouette, centre-frame
- **Red bounding box**: thick (2–3px) red rectangle around the drone — YOLOv8 detection output
- **Track label above box**: small dark rounded rectangle with white "23" and a miniature drone icon inside

### No overlaid HUD elements on the feed itself — the bounding box and label are the only overlays.

---

## Zone 3a — Telemetry Table

### Column headers
Small uppercase, `text-secondary`, ~11px, spaced with `letter-spacing: 0.05em`:
`#` | `TARGET DESCRIPTION` | `DETECTED AT` | `DETECTED BY` | `COORDS` | `DISTANCE` | `HEADING` | `ACTIONS`

### Row style
- Height: ~26px per row
- Background: `bg-base`, alternating or flat — very subtle distinction
- **Selected row** (ID 23): `bg-raised`, slightly lighter
- Bottom border: `1px solid border`
- Font: `text-primary`, 12px, regular weight
- ID column: bold, monospace
- Coordinate, distance, heading columns: monospace `text-mono`

### Data columns
| Column | Format | Example |
|--------|--------|---------|
| `#` | integer, bold | `23` |
| TARGET DESCRIPTION | plain text | `Attack Drone`, `armed person` |
| DETECTED AT | `HH:MM:SS` | `10:35:22` |
| DETECTED BY | sensor ID | `LAV1`, `LAV2` |
| COORDS | `NNNNNNe/NNNNNNn` | `123456E/123456N` |
| DISTANCE | `Nm` | `1405m` |
| HEADING | `NNN°` | `320°` |
| ACTIONS | buttons | see below |

### Action buttons
Two states:

**LOCK ON** — unconfirmed target:
- Small outlined pill button, ~60×20px
- Border: `btn-lock` (`#f0a020`), 1px
- Text: "LOCK ON", `btn-lock` colour, 11px bold
- No fill (transparent background)
- Right of LOCK ON: two small icon buttons — pin (bookmark) and arrow (navigate-to)

**RELEASE** — currently locked target (row 23):
- Filled pill button, same size
- Background: `btn-release` (`#7b5ea7`)
- Text: "RELEASE", white, 11px bold
- Small icon to left of text (lock or unlock symbol)
- Pin and arrow icon buttons follow to the right

---

## Zone 3b — Target Detail Panel

Shown when a target is locked. Structured as three sub-sections vertically.

### Header
- `bg-raised` strip
- Left: **red rounded tag** "23" (small, `accent-threat` bg, white text) + "Attack Drone" white text, medium weight
- Right: three-dot or list icon (more options)

### Stats row
Single line below header, `text-secondary`, ~11px:
- Coordinates: `26.4464 N / 515653 E`
- Icon + `A 320°` — heading
- Icon + `50km/h` — speed
- Icon + `↕ 15m` — altitude AGL
- `1405m` — slant range

### Body — two columns
**Left column (~40%):** camera thumbnail
- Small image (~80×60px) — live or still from camera feed
- **Red crosshair reticle** overlaid, centred on drone — thin lines with gap at centre
- Dark frame around image

**Right column (~60%):** weapon options — three rows, each:
- Text: "**Reshef 1**" (effector platform name) + " / " + "**JAM**" / "**PB**" / "**SPO**" (engagement type)
- **[APPROVE!]** button: filled pill, `btn-approve` (`#e8920a`), white bold text, full row width

### Footer
- **[SEND TO EFFECTOR...]** full-width button
- Background: `btn-send` (`#1a6080`)
- White text, 12px, uppercase
- Slight top border separator

---

## Typography

| Use | Font style | Size | Weight |
|-----|-----------|------|--------|
| Data values (distance, heading) | Monospace | 12px | Regular |
| Column headers | Sans-serif, uppercase | 11px | Regular, letter-spaced |
| Track labels on map | Sans-serif | 11px | Regular |
| Target detail stats | Sans-serif | 11px | Regular |
| Button text | Sans-serif, uppercase | 11px | Bold |
| ID column | Monospace | 12px | Bold |
| Mission name (top bar) | Sans-serif | 13px | Medium |
| Clock | Sans-serif | 14px | Bold |

Overall impression: **Inter** or **IBM Plex Sans** + **IBM Plex Mono** (or Roboto + Roboto Mono). The system is functional-dense — every pixel earns its place.

---

## Interaction Model

1. **Drones appear as blips** on map as they enter radar range
2. **LOCK ON** button in telemetry row → promotes to RELEASE state, opens Target Detail panel
3. **Target Detail panel** shows live camera thumbnail, stats, and effector options
4. Each effector row has an **APPROVE!** button — two-step confirmation before engaging
5. **SEND TO EFFECTOR** commits the selected engagement
6. On map, locked target turns red, vector line drawn from base to drone
7. Camera feed auto-switches to show the locked target ("Stinger [LIVE]")

---

## Key Design Principles

- **Information density over whitespace** — every zone is packed; margins are ~4–8px
- **Colour carries state** — blue = tracking, red = threat/locked; no ambiguity
- **Two-step engagement** — LOCK ON → APPROVE → SEND prevents accidental fire
- **Persistent satellite context** — map always shows real terrain, overlays are transparent
- **Split-view parity** — map + camera feed always visible simultaneously; neither collapses by default
- **Monospace for numbers** — all telemetry values use monospace to prevent layout jitter as values change
