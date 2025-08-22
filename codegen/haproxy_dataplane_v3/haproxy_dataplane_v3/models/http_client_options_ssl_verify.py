from enum import Enum


class HttpClientOptionsSslVerify(str, Enum):
    NONE = "none"
    REQUIRED = "required"
    VALUE_0 = ""

    def __str__(self) -> str:
        return str(self.value)
