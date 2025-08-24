from enum import Enum


class BindParamsQuicSocket(str, Enum):
    CONNECTION = "connection"
    LISTENER = "listener"

    def __str__(self) -> str:
        return str(self.value)
