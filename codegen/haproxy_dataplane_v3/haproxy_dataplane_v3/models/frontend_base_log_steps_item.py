from enum import Enum


class FrontendBaseLogStepsItem(str, Enum):
    ACCEPT = "accept"
    ANY = "any"
    CLOSE = "close"
    CONNECT = "connect"
    ERROR = "error"
    REQUEST = "request"
    RESPONSE = "response"

    def __str__(self) -> str:
        return str(self.value)
