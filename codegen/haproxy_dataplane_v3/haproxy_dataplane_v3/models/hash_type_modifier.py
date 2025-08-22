from enum import Enum


class HashTypeModifier(str, Enum):
    AVALANCHE = "avalanche"

    def __str__(self) -> str:
        return str(self.value)
