from enum import Enum


class HashTypeMethod(str, Enum):
    CONSISTENT = "consistent"
    MAP_BASED = "map-based"

    def __str__(self) -> str:
        return str(self.value)
