from enum import Enum


class CookieType(str, Enum):
    INSERT = "insert"
    PREFIX = "prefix"
    REWRITE = "rewrite"

    def __str__(self) -> str:
        return str(self.value)
