from enum import Enum


class CompressionDirection(str, Enum):
    BOTH = "both"
    REQUEST = "request"
    RESPONSE = "response"

    def __str__(self) -> str:
        return str(self.value)
