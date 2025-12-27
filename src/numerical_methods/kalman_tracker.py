import numpy as np
from typing import Tuple
from .base_tracker import Base

class KalmanFilterTracker(Base):

    # State: [x, y, vx, vy]

    def __init__(self):
        # PREDIKSI KEMANA
        self.F = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)

        # KAMERA LIAT APA (X,Y)
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
        ], dtype=np.float32)

        # SEBERAPA HALUS / PERCAYA MODEL vs SENSOR
        self.Q = np.eye(4, dtype=np.float32) * 0.03  # process noise - model
        self.R = np.eye(2, dtype=np.float32) * 0.1   # measurement noise - sensor

        # STATE & COVARIANCE
        self.x = np.zeros((4, 1), dtype=np.float32)      # [x, y, vx, vy]^T
        self.P = np.eye(4, dtype=np.float32) * 10        # covariance 4x4
        self.initialized = False

    def apply(self, x: float, y: float) -> Tuple[float, float]:
        # measurement vector (2x1)
        z = np.array([[x], [y]], dtype=np.float32)

        if not self.initialized:
            self.x[0, 0] = x
            self.x[1, 0] = y
            self.initialized = True
            return x, y

        # PREDICT (time update)
        self.x = self.F @ self.x                          # x̂ = F x
        self.P = self.F @ self.P @ self.F.T + self.Q      # P̂ = F P F^T + Q

        # INNOVATION (measurement update)
        y_tilde = z - self.H @ self.x                     # y = z - H x̂
        S = self.H @ self.P @ self.H.T + self.R           # S = H P̂ H^T + R

        # KALMAN GAIN
        K = self.P @ self.H.T @ np.linalg.inv(S)          # K = P̂ H^T S^-1

        # UPDATE STATE
        self.x = self.x + K @ y_tilde                     # x = x̂ + K y

        # UPDATE COVARIANCE
        I = np.eye(4, dtype=np.float32)
        self.P = (I - K @ self.H) @ self.P                # P = (I - K H) P̂

        return float(self.x[0, 0]), float(self.x[1, 0])

    def get_velocity(self) -> Tuple[float, float]:
        return float(self.x[2, 0]), float(self.x[3, 0])

    def get_name(self) -> str:
        return "Kalman Filter"