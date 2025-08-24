from enum import Enum


class TCPCheckToutStatus(str, Enum):
    L4TOUT = "L4TOUT"
    L6TOUT = "L6TOUT"
    L7TOUT = "L7TOUT"

    def __str__(self) -> str:
        return str(self.value)
