from enum import Enum


class ConfigurationTransactionStatus(str, Enum):
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    OUTDATED = "outdated"
    SUCCESS = "success"

    def __str__(self) -> str:
        return str(self.value)
