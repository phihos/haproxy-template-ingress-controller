from enum import Enum


class HashTypeFunction(str, Enum):
    CRC32 = "crc32"
    DJB2 = "djb2"
    NONE = "none"
    SDBM = "sdbm"
    WT6 = "wt6"

    def __str__(self) -> str:
        return str(self.value)
