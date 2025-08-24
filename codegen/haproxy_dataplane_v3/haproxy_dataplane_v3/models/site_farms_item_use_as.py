from enum import Enum


class SiteFarmsItemUseAs(str, Enum):
    CONDITIONAL = "conditional"
    DEFAULT = "default"

    def __str__(self) -> str:
        return str(self.value)
