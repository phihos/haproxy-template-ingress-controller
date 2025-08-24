from enum import Enum


class TuneOptionsEpollMaskEventsItem(str, Enum):
    ERR = "err"
    HUP = "hup"
    RDHUP = "rdhup"

    def __str__(self) -> str:
        return str(self.value)
