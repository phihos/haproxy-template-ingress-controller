from enum import Enum


class ConfigStickTableSrvkey(str, Enum):
    ADDR = "addr"
    NAME = "name"

    def __str__(self) -> str:
        return str(self.value)
