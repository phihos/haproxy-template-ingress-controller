from enum import Enum


class ClusterSettingsMode(str, Enum):
    CLUSTER = "cluster"
    SINGLE = "single"

    def __str__(self) -> str:
        return str(self.value)
