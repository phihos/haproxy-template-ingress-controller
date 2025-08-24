from enum import Enum


class TuneQuicOptionsSocketOwner(str, Enum):
    CONNECTION = "connection"
    LISTENER = "listener"

    def __str__(self) -> str:
        return str(self.value)
