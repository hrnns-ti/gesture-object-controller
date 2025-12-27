from typing import Tuple
from .base_tracker import Base

class ExponentialSmoothing(Base):

    # x_smooth(t) = α * x_raw(t) + (1 - α) * x_smooth(t-1)

    def __init__(self, alpha: float = 0.7):
        self.alpha = alpha
        self.prev_x: float = 0.0
        self.prev_y: float = 0.0
        self.initialized = False

    def apply(self, x: float, y: float) -> Tuple[float, float]:
        if not self.initialized:
            self.prev_x = x
            self.prev_y = y
            self.initialized = True
            return x, y

        self.prev_x = self.alpha * x + (1 - self.alpha) * self.prev_x
        self.prev_y = self.alpha * y + (1 - self.alpha) * self.prev_y
        return self.prev_x, self.prev_y

    def get_name(self) -> str:
        return f"Exponential Smoothing (α={self.alpha})"
