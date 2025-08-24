from enum import Enum


class HAProxyReloadStatus(str, Enum):
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"

    def __str__(self) -> str:
        return str(self.value)
