from enum import Enum


class ClusterSettingsStatus(str, Enum):
    ACTIVE = "active"
    UNREACHABLE = "unreachable"
    WAITING_APPROVAL = "waiting_approval"

    def __str__(self) -> str:
        return str(self.value)
