from enum import Enum


class TuneLuaOptionsBoolSampleConversion(str, Enum):
    NORMAL = "normal"
    PRE_3_1_BUG = "pre-3.1-bug"

    def __str__(self) -> str:
        return str(self.value)
