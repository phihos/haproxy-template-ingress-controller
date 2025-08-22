from enum import Enum


class StickTableFieldsItemType(str, Enum):
    COUNTER = "counter"
    RATE = "rate"

    def __str__(self) -> str:
        return str(self.value)
