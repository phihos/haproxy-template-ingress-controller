from enum import Enum


class TuneOptionsTakeoverOtherTgConnections(str, Enum):
    FULL = "full"
    NONE = "none"
    RESTRICTED = "restricted"

    def __str__(self) -> str:
        return str(self.value)
