from enum import Enum


class TuneOptionsListenerDefaultShards(str, Enum):
    BY_GROUP = "by-group"
    BY_PROCESS = "by-process"
    BY_THREAD = "by-thread"

    def __str__(self) -> str:
        return str(self.value)
