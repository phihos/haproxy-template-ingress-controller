from enum import Enum


class SPOEAgentForceSetVar(str, Enum):
    ENABLED = "enabled"

    def __str__(self) -> str:
        return str(self.value)
