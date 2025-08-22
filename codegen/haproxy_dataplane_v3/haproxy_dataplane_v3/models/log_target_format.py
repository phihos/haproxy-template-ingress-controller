from enum import Enum


class LogTargetFormat(str, Enum):
    ISO = "iso"
    LOCAL = "local"
    PRIORITY = "priority"
    RAW = "raw"
    RFC3164 = "rfc3164"
    RFC5424 = "rfc5424"
    SHORT = "short"
    TIMED = "timed"

    def __str__(self) -> str:
        return str(self.value)
