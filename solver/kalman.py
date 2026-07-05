"""
Per-track Kalman filter. Constant-velocity model, 3D position measurements.
State: [x, y, z, vx, vy, vz]. No ROS deps.
"""
import numpy as np

# Process noise: model untracked acceleration as white noise.
# sigma_a = 5 m/s² matches drone max-accel constraint from sim config.
SIGMA_A = 5.0
# Measurement noise: ~5m position uncertainty (image projection / sensor error).
SIGMA_R = 5.0


def _F(dt: float) -> np.ndarray:
    """State transition matrix for constant-velocity model."""
    F = np.eye(6)
    F[0, 3] = F[1, 4] = F[2, 5] = dt
    return F


def _Q(dt: float, sigma_a: float = SIGMA_A) -> np.ndarray:
    """Process noise covariance (discrete white-noise acceleration model)."""
    q = np.array([
        [dt**4 / 4, dt**3 / 2],
        [dt**3 / 2, dt**2],
    ]) * sigma_a**2
    Q = np.zeros((6, 6))
    for i in range(3):
        Q[np.ix_([i, i+3], [i, i+3])] = q
    return Q


_H = np.array([  # measurement matrix: observe position only
    [1, 0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0],
], dtype=float)

_R = np.eye(3) * SIGMA_R**2  # measurement noise covariance


class KalmanTrack:
    """
    Single-target Kalman filter. Call predict() each frame, then update()
    when a detection is associated. Call predict() alone for coasting frames.
    """

    def __init__(self, pos: np.ndarray, vel: np.ndarray | None = None):
        self.x = np.zeros(6)
        self.x[:3] = pos
        self.x[3:] = vel if vel is not None else np.zeros(3)
        self.P = np.eye(6) * 100.0  # loose initial covariance

    def predict(self, dt: float = 1/30) -> np.ndarray:
        F = _F(dt)
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + _Q(dt)
        return self.x[:3].copy()

    def update(self, measurement: np.ndarray) -> np.ndarray:
        S = _H @ self.P @ _H.T + _R
        K = self.P @ _H.T @ np.linalg.inv(S)
        self.x = self.x + K @ (measurement - _H @ self.x)
        self.P = (np.eye(6) - K @ _H) @ self.P
        return self.x[:3].copy()

    @property
    def pos(self) -> np.ndarray:
        return self.x[:3].copy()

    @property
    def vel(self) -> np.ndarray:
        return self.x[3:].copy()

    @property
    def covariance(self) -> np.ndarray:
        return self.P.copy()


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    dt = 1 / 30

    # Drone flying a circle: radius 500m, period 60s
    true_pos, filtered_pos, raw_pos = [], [], []
    kf = KalmanTrack(np.array([500.0, 0.0, 100.0]))

    omega = 2 * np.pi / 60  # rad/s
    for i in range(90):  # 3 seconds @ 30fps
        t = i * dt
        truth = np.array([500 * np.cos(omega * t), 500 * np.sin(omega * t), 100.0])
        noisy = truth + rng.normal(0, SIGMA_R, 3)

        kf.predict(dt)
        filtered = kf.update(noisy)

        true_pos.append(truth)
        raw_pos.append(noisy)
        filtered_pos.append(filtered)

    true_pos = np.array(true_pos)
    raw_pos = np.array(raw_pos)
    filtered_pos = np.array(filtered_pos)

    raw_err = float(np.mean(np.linalg.norm(raw_pos - true_pos, axis=1)))
    filt_err = float(np.mean(np.linalg.norm(filtered_pos - true_pos, axis=1)))

    print(f"Mean position error — raw: {raw_err:.2f}m  filtered: {filt_err:.2f}m")
    assert filt_err < raw_err, "Kalman filter should reduce measurement noise"

    # Check velocity estimate is in the right ballpark
    true_vel = np.array([
        -500 * omega * np.sin(omega * 89 * dt),
         500 * omega * np.cos(omega * 89 * dt),
         0.0
    ])
    vel_err = float(np.linalg.norm(kf.vel - true_vel))
    print(f"Velocity estimate error at t=3s: {vel_err:.2f} m/s (true speed {np.linalg.norm(true_vel):.2f} m/s)")
    assert vel_err < 10.0, "velocity estimate too far off"

    print("OK")
