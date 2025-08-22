from enum import Enum


class RuntimeAddServerObserve(str, Enum):
    LAYER4 = "layer4"
    LAYER7 = "layer7"

    def __str__(self) -> str:
        return str(self.value)
