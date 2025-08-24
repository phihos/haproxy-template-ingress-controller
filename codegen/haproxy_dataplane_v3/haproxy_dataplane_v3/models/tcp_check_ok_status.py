from enum import Enum


class TCPCheckOkStatus(str, Enum):
    L4OK = "L4OK"
    L6OK = "L6OK"
    L7OK = "L7OK"
    L7OKC = "L7OKC"

    def __str__(self) -> str:
        return str(self.value)
