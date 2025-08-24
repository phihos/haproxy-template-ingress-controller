from enum import Enum


class BackendBaseIgnorePersistListItemCond(str, Enum):
    IF = "if"
    UNLESS = "unless"

    def __str__(self) -> str:
        return str(self.value)
