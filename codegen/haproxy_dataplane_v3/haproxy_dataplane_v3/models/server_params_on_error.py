from enum import Enum


class ServerParamsOnError(str, Enum):
    FAIL_CHECK = "fail-check"
    FASTINTER = "fastinter"
    MARK_DOWN = "mark-down"
    SUDDEN_DEATH = "sudden-death"

    def __str__(self) -> str:
        return str(self.value)
