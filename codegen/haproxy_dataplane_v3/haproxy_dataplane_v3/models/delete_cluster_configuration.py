from enum import Enum


class DeleteClusterConfiguration(str, Enum):
    KEEP = "keep"

    def __str__(self) -> str:
        return str(self.value)
