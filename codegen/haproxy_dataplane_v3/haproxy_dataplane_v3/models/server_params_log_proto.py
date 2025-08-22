from enum import Enum


class ServerParamsLogProto(str, Enum):
    LEGACY = "legacy"
    OCTET_COUNT = "octet-count"

    def __str__(self) -> str:
        return str(self.value)
