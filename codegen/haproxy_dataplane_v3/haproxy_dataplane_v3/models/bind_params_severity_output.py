from enum import Enum


class BindParamsSeverityOutput(str, Enum):
    NONE = "none"
    NUMBER = "number"
    STRING = "string"

    def __str__(self) -> str:
        return str(self.value)
