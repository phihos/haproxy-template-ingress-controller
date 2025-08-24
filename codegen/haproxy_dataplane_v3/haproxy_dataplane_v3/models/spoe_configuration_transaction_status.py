from enum import Enum


class SPOEConfigurationTransactionStatus(str, Enum):
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"

    def __str__(self) -> str:
        return str(self.value)
