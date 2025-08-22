from enum import Enum


class TCPCheckErrorStatus(str, Enum):
    L4CON = "L4CON"
    L6RSP = "L6RSP"
    L7OKC = "L7OKC"
    L7RSP = "L7RSP"
    L7STS = "L7STS"

    def __str__(self) -> str:
        return str(self.value)
