from enum import Enum


class ConsulServerHealthCheckPolicy(str, Enum):
    ALL = "all"
    ANY = "any"
    MIN = "min"
    NONE = "none"

    def __str__(self) -> str:
        return str(self.value)
