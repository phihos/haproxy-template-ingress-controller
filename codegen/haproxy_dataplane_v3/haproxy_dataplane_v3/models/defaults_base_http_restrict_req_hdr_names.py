from enum import Enum


class DefaultsBaseHttpRestrictReqHdrNames(str, Enum):
    DELETE = "delete"
    PRESERVE = "preserve"
    REJECT = "reject"

    def __str__(self) -> str:
        return str(self.value)
