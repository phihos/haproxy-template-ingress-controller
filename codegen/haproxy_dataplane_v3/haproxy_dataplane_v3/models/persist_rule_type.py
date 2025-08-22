from enum import Enum


class PersistRuleType(str, Enum):
    RDP_COOKIE = "rdp-cookie"

    def __str__(self) -> str:
        return str(self.value)
