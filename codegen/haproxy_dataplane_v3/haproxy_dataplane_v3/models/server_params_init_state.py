from enum import Enum


class ServerParamsInitState(str, Enum):
    DOWN = "down"
    FULLY_DOWN = "fully-down"
    FULLY_UP = "fully-up"
    UP = "up"

    def __str__(self) -> str:
        return str(self.value)
