from enum import Enum


class ConsulServerServerSlotsGrowthType(str, Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"

    def __str__(self) -> str:
        return str(self.value)
