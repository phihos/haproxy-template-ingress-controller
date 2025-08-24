from enum import Enum


class HTTPResponseRuleRedirType(str, Enum):
    LOCATION = "location"
    PREFIX = "prefix"
    SCHEME = "scheme"

    def __str__(self) -> str:
        return str(self.value)
