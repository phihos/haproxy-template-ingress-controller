from enum import Enum


class GetAllSpoeTransactionStatus(str, Enum):
    FAILED = "failed"
    IN_PROGRESS = "in_progress"

    def __str__(self) -> str:
        return str(self.value)
