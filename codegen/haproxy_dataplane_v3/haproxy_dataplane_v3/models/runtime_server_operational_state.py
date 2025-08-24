from enum import Enum


class RuntimeServerOperationalState(str, Enum):
    DOWN = "down"
    STOPPING = "stopping"
    UP = "up"

    def __str__(self) -> str:
        return str(self.value)
