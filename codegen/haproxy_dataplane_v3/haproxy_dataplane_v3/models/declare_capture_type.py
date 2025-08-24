from enum import Enum


class DeclareCaptureType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"

    def __str__(self) -> str:
        return str(self.value)
