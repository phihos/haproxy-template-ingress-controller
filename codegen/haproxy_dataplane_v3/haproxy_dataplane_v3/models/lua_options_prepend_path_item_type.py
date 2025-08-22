from enum import Enum


class LuaOptionsPrependPathItemType(str, Enum):
    CPATH = "cpath"
    PATH = "path"

    def __str__(self) -> str:
        return str(self.value)
