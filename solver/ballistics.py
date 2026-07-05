"""
Ballistics solver: intercept geometry and threat scoring.
No ROS deps — runs standalone.

Coordinate convention: x=north, y=west, z=up (ROS REP-103)
Bearing: degrees clockwise from north. Elevation: degrees above horizon.
"""
import math
import numpy as np


DEFAULT_MUZZLE_VEL = 1000.0  # m/s


def intercept_time(r: np.ndarray, v: np.ndarray, muzzle_vel: float = DEFAULT_MUZZLE_VEL) -> float | None:
    """
    Solve for time-to-intercept given relative position r and drone velocity v.
    Quadratic: t²(|v|²-V²) + 2t(r·v) + |r|² = 0
    Returns smallest positive root, or None if no solution.
    """
    a = np.dot(v, v) - muzzle_vel ** 2
    b = 2 * np.dot(r, v)
    c = np.dot(r, r)

    if abs(a) < 1e-9:  # drone speed negligible vs muzzle vel
        if abs(b) < 1e-9:
            return None
        t = -c / b
        return t if t > 0 else None

    disc = b ** 2 - 4 * a * c
    if disc < 0:
        return None

    sqrt_disc = math.sqrt(disc)
    t1 = (-b - sqrt_disc) / (2 * a)
    t2 = (-b + sqrt_disc) / (2 * a)
    candidates = [t for t in (t1, t2) if t > 0]
    return min(candidates) if candidates else None


def solve(turret_pos: np.ndarray, drone_pos: np.ndarray, drone_vel: np.ndarray,
          muzzle_vel: float = DEFAULT_MUZZLE_VEL) -> dict:
    """
    Compute full ballistic solution for one drone.

    Returns dict with: bearing_deg, elevation_deg, range_m, aim_point,
                       time_to_impact (None if no solution)
    """
    r = drone_pos - turret_pos
    range_m = float(np.linalg.norm(r))

    t = intercept_time(r, drone_vel, muzzle_vel)

    if t is not None:
        aim_point = drone_pos + drone_vel * t
        aim_vec = aim_point - turret_pos
    else:
        aim_point = drone_pos  # ponytail: fall back to current position if unsolvable
        aim_vec = r

    horiz = math.sqrt(aim_vec[0] ** 2 + aim_vec[1] ** 2)
    # bearing: clockwise from north (x-axis), y is left so negate y
    bearing_deg = math.degrees(math.atan2(-aim_vec[1], aim_vec[0])) % 360
    elevation_deg = math.degrees(math.atan2(aim_vec[2], horiz))

    return {
        "bearing_deg": bearing_deg,
        "elevation_deg": elevation_deg,
        "range_m": range_m,
        "aim_point": aim_point,
        "time_to_impact": t,
    }


def threat_score(range_m: float, speed: float, bearing_rate_deg_s: float = 0.0) -> float:
    """
    Higher = more urgent. Closest + fastest + stable bearing wins.
    ponytail: bearing stability term is simple inverse; refine with track history when available.
    """
    if range_m <= 0:
        return float("inf")
    stability = 1.0 / (1.0 + bearing_rate_deg_s)
    return (speed / range_m) * stability


def rank_threats(solutions: list[dict]) -> list[dict]:
    """Sort solutions list in-place by threat score descending. Returns same list."""
    solutions.sort(key=lambda s: s.get("threat_score", 0), reverse=True)
    return solutions


if __name__ == "__main__":
    # Self-check: stationary turret at origin, drone 1km north at 50m alt moving east at 20 m/s
    turret = np.array([0.0, 0.0, 0.0])
    drone = np.array([1000.0, 0.0, 50.0])
    vel = np.array([0.0, -20.0, 0.0])  # eastward (negative y in REP-103)

    sol = solve(turret, drone, vel)
    print(f"Bearing:    {sol['bearing_deg']:.2f}°  (expect ~north, slight east)")
    print(f"Elevation:  {sol['elevation_deg']:.2f}°")
    print(f"Range:      {sol['range_m']:.1f}m")
    print(f"ToF:        {sol['time_to_impact']:.4f}s")

    # Sanity: projectile reaches aim_point in time_to_impact
    t = sol["time_to_impact"]
    aim = sol["aim_point"]
    proj_dist = float(np.linalg.norm(aim - turret))
    assert abs(proj_dist - DEFAULT_MUZZLE_VEL * t) < 0.1, "intercept geometry broken"

    score = threat_score(sol["range_m"], float(np.linalg.norm(vel)))
    print(f"Threat score: {score:.6f}")
    print("OK")
