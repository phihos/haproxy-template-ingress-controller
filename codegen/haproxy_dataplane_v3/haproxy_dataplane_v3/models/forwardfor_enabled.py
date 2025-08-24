from enum import Enum


class ForwardforEnabled(str, Enum):
    ENABLED = "enabled"

    def __str__(self) -> str:
        return str(self.value)
