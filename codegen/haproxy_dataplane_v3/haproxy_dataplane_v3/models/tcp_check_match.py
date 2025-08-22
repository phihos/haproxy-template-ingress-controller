from enum import Enum


class TCPCheckMatch(str, Enum):
    BINARY = "binary"
    BINARY_LF = "binary-lf"
    RBINARY = "rbinary"
    RSTRING = "rstring"
    STRING = "string"
    STRING_LF = "string-lf"

    def __str__(self) -> str:
        return str(self.value)
