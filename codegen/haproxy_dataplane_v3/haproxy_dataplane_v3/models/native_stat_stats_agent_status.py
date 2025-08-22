from enum import Enum


class NativeStatStatsAgentStatus(str, Enum):
    INI = "INI"
    L4CON = "L4CON"
    L4OK = "L4OK"
    L4TOUT = "L4TOUT"
    L7OK = "L7OK"
    L7STS = "L7STS"
    SOCKERR = "SOCKERR"
    UNK = "UNK"

    def __str__(self) -> str:
        return str(self.value)
