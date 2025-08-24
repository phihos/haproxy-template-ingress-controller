from enum import Enum


class SslOptionsServerVerify(str, Enum):
    NONE = "none"
    REQUIRED = "required"

    def __str__(self) -> str:
        return str(self.value)
