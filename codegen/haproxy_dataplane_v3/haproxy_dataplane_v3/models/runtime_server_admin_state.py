from enum import Enum


class RuntimeServerAdminState(str, Enum):
    DRAIN = "drain"
    MAINT = "maint"
    READY = "ready"

    def __str__(self) -> str:
        return str(self.value)
