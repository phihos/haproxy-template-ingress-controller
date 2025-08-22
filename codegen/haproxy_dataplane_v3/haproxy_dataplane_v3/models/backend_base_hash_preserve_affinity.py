from enum import Enum


class BackendBaseHashPreserveAffinity(str, Enum):
    ALWAYS = "always"
    MAXCONN = "maxconn"
    MAXQUEUE = "maxqueue"

    def __str__(self) -> str:
        return str(self.value)
