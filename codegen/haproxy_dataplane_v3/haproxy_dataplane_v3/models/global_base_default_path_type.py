from enum import Enum


class GlobalBaseDefaultPathType(str, Enum):
    CONFIG = "config"
    CURRENT = "current"
    ORIGIN = "origin"
    PARENT = "parent"

    def __str__(self) -> str:
        return str(self.value)
