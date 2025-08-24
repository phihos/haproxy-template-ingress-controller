from enum import Enum


class HTTPRequestRuleReturnContentFormat(str, Enum):
    DEFAULT_ERRORFILES = "default-errorfiles"
    ERRORFILE = "errorfile"
    ERRORFILES = "errorfiles"
    FILE = "file"
    LF_FILE = "lf-file"
    LF_STRING = "lf-string"
    STRING = "string"

    def __str__(self) -> str:
        return str(self.value)
