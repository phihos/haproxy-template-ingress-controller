from enum import Enum


class NativeStatStatsCheckStatus(str, Enum):
    INI = "INI"
    L4CON = "L4CON"
    L4OK = "L4OK"
    L4TOUT = "L4TOUT"
    L6OK = "L6OK"
    L6RSP = "L6RSP"
    L6TOUT = "L6TOUT"
    L7OK = "L7OK"
    L7OKC = "L7OKC"
    L7RSP = "L7RSP"
    L7STS = "L7STS"
    L7TOUT = "L7TOUT"
    SOCKERR = "SOCKERR"
    UNK = "UNK"

    def __str__(self) -> str:
        return str(self.value)
