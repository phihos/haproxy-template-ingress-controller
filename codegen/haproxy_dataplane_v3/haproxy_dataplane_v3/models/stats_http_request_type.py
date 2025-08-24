from enum import Enum


class StatsHttpRequestType(str, Enum):
    ALLOW = "allow"
    AUTH = "auth"
    DENY = "deny"

    def __str__(self) -> str:
        return str(self.value)
