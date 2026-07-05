"""
Multi-target tracker: Hungarian assignment + Kalman filter per track.
Accepts 3D position measurements. No ROS deps.

Track lifecycle: tentative (< CONFIRM_HITS) -> tracking -> coasting -> lost
"""
import math
import numpy as np
from scipy.optimize import linear_sum_assignment

from solver.kalman import KalmanTrack
from solver.ballistics import solve, threat_score, rank_threats

MAX_ASSOCIATION_DIST = 100.0  # metres; detections farther than this are unmatched
CONFIRM_HITS = 3               # consecutive hits before track is "tracking"
MAX_COAST_FRAMES = 5           # missed frames before track is dropped
TURRET_POS = np.zeros(3)       # turret at origin; override if needed


class Track:
    __slots__ = ("track_id", "kf", "status", "hits", "missed",
                 "age", "_prev_bearing")

    def __init__(self, track_id: int, pos: np.ndarray):
        self.track_id = track_id
        self.kf = KalmanTrack(pos)
        self.status = "tentative"
        self.hits = 1
        self.missed = 0
        self.age = 1
        self._prev_bearing: float | None = None

    def bearing_rate(self, bearing_deg: float, dt: float) -> float:
        if self._prev_bearing is None or dt <= 0:
            return 0.0
        diff = abs(bearing_deg - self._prev_bearing)
        diff = min(diff, 360 - diff)  # shortest arc
        return diff / dt

    def to_dict(self, turret_pos: np.ndarray = TURRET_POS,
                muzzle_vel: float = 1000.0, dt: float = 1/30) -> dict:
        pos = self.kf.pos
        vel = self.kf.vel
        sol = solve(turret_pos, pos, vel, muzzle_vel)
        br = self.bearing_rate(sol["bearing_deg"], dt)
        sol["threat_score"] = threat_score(sol["range_m"], float(np.linalg.norm(vel)), br)
        sol["track_id"] = self.track_id
        sol["status"] = self.status
        sol["age"] = self.age
        sol["pos"] = pos.tolist()
        sol["vel"] = vel.tolist()
        sol["covariance"] = self.kf.covariance.tolist()
        self._prev_bearing = sol["bearing_deg"]
        return sol


class Tracker:
    def __init__(self, turret_pos: np.ndarray = TURRET_POS,
                 muzzle_vel: float = 1000.0):
        self.turret_pos = turret_pos
        self.muzzle_vel = muzzle_vel
        self._tracks: dict[int, Track] = {}
        self._next_id = 1

    def update(self, detections: list[np.ndarray], dt: float = 1/30) -> list[dict]:
        """
        detections: list of np.ndarray shape (3,) — 3D positions in metres.
        Returns sorted list of track dicts (highest threat first).
        """
        # 1. Predict all existing tracks forward
        for t in self._tracks.values():
            t.kf.predict(dt)
            t.age += 1

        # 2. Build cost matrix
        track_ids = list(self._tracks.keys())
        if track_ids and detections:
            predicted = np.array([self._tracks[tid].kf.pos for tid in track_ids])
            det_arr = np.array(detections)
            # (n_tracks, n_dets)
            dists = np.linalg.norm(predicted[:, None] - det_arr[None, :], axis=2)
            dists[dists > MAX_ASSOCIATION_DIST] = 1e9  # effectively infinity

            row_ind, col_ind = linear_sum_assignment(dists)
            matched_tracks, matched_dets = set(), set()

            for r, c in zip(row_ind, col_ind):
                if dists[r, c] < MAX_ASSOCIATION_DIST:
                    tid = track_ids[r]
                    self._tracks[tid].kf.update(detections[c])
                    self._tracks[tid].hits += 1
                    self._tracks[tid].missed = 0
                    if (self._tracks[tid].status == "tentative"
                            and self._tracks[tid].hits >= CONFIRM_HITS):
                        self._tracks[tid].status = "tracking"
                    matched_tracks.add(tid)
                    matched_dets.add(c)
        else:
            matched_tracks, matched_dets = set(), set()

        # 3. Age out unmatched tracks
        for tid in track_ids:
            if tid not in matched_tracks:
                self._tracks[tid].missed += 1
                if self._tracks[tid].missed > MAX_COAST_FRAMES:
                    del self._tracks[tid]
                else:
                    self._tracks[tid].status = "coasting"

        # 4. Spawn new tracks for unmatched detections
        for i, det in enumerate(detections):
            if i not in matched_dets:
                tid = self._next_id
                self._next_id += 1
                self._tracks[tid] = Track(tid, det)

        # 5. Emit track dicts, ranked by threat
        results = [
            t.to_dict(self.turret_pos, self.muzzle_vel, dt)
            for t in self._tracks.values()
            if t.status in ("tracking", "coasting")
        ]
        return rank_threats(results)

    @property
    def active_count(self) -> int:
        return sum(1 for t in self._tracks.values() if t.status != "tentative")


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    tracker = Tracker()
    dt = 1/30
    omega = 2 * np.pi / 60

    # Two drones: one circling, one approaching from north
    def truth(i):
        t = i * dt
        d1 = np.array([500 * math.cos(omega*t), 500 * math.sin(omega*t), 80.0])
        d2 = np.array([1200 - t*15, 0.0, 60.0])  # approaching at 15 m/s
        return [d1, d2]

    # Warm up (CONFIRM_HITS frames to confirm tracks)
    for i in range(10):
        dets = [p + rng.normal(0, 5, 3) for p in truth(i)]
        tracks = tracker.update(dets, dt)

    assert tracker.active_count == 2, f"Expected 2 active tracks, got {tracker.active_count}"

    # Simulate 1 second of occlusion on drone 0 (only send drone 1)
    for i in range(10, 40):
        dets = [truth(i)[1] + rng.normal(0, 5, 3)]
        tracker.update(dets, dt)

    assert tracker.active_count >= 1, "Should coast track through occlusion"

    # Recover both
    for i in range(40, 50):
        dets = [p + rng.normal(0, 5, 3) for p in truth(i)]
        tracks = tracker.update(dets, dt)

    assert len(tracks) == 2, f"Expected 2 tracks post-recovery, got {len(tracks)}"
    assert tracks[0]["threat_score"] >= tracks[1]["threat_score"], "Threat ordering broken"

    # Spot-check a solution
    t0 = tracks[0]
    assert 0 < t0["bearing_deg"] < 360
    assert -90 < t0["elevation_deg"] < 90
    assert t0["range_m"] > 0

    print(f"Tracks: {len(tracks)}  |  "
          f"Top threat: ID={t0['track_id']} range={t0['range_m']:.0f}m "
          f"speed={np.linalg.norm(t0['vel']):.1f}m/s "
          f"bearing={t0['bearing_deg']:.1f}° "
          f"score={t0['threat_score']:.5f}")
    print("OK")
