from enum import Enum


class ServerParamsVerify(str, Enum):
    NONE = "none"
    REQUIRED = "required"

    def __str__(self) -> str:
        return str(self.value)
