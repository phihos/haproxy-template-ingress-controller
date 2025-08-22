from enum import Enum


class ServerSwitchingRuleCond(str, Enum):
    IF = "if"
    UNLESS = "unless"

    def __str__(self) -> str:
        return str(self.value)
