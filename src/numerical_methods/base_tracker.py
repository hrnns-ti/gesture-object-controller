from abc import ABC, abstractmethod
from typing import Tuple

class Base(ABC):
    @abstractmethod
    def apply(self, x: float, y: float) -> Tuple[float, float]:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass