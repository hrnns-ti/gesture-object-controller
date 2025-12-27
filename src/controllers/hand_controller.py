from typing import Tuple
from ..numerical_methods import KalmanFilterTracker, ExponentialSmoothing

class HandTrackingController:
    def __init__(self):
        self.kalman = KalmanFilterTracker()
        self.smoothing = ExponentialSmoothing(alpha = 0.7)

        # 1 = Raw || 2 = Kalman || 3 = Smoothing
        self.mode = 2

    def set_mode(self, mode: int) -> None:
        if mode in (1, 2, 3):
            self.mode = mode

    def process(self, x: float, y: float) -> Tuple[float, float]:
        if self.mode == 1:
            return x, y
        elif self.mode == 2:
            return self.smoothing.apply(x, y)
        else:
            return self.kalman.apply(x, y)
