from enum import Enum


class TableType(str, Enum):
    BINARY = "binary"
    INTEGER = "integer"
    IP = "ip"
    STRING = "string"

    def __str__(self) -> str:
        return str(self.value)
