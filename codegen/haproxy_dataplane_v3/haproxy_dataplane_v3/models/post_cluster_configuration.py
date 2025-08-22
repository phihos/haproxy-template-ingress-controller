from enum import Enum


class PostClusterConfiguration(str, Enum):
    KEEP = "keep"

    def __str__(self) -> str:
        return str(self.value)
