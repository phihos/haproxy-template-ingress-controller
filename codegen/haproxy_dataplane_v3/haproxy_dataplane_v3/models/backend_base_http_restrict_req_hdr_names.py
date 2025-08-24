from enum import Enum


class BackendBaseHttpRestrictReqHdrNames(str, Enum):
    DELETE = "delete"
    PRESERVE = "preserve"
    REJECT = "reject"

    def __str__(self) -> str:
        return str(self.value)
