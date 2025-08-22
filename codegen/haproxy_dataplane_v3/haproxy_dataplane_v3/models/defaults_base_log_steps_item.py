from enum import Enum


class DefaultsBaseLogStepsItem(str, Enum):
    ACCEPT = "accept"
    ANY = "any"
    CLOSE = "close"
    CONNECT = "connect"
    ERROR = "error"
    REQUEST = "request"
    RESPONSE = "response"

    def __str__(self) -> str:
        return str(self.value)
