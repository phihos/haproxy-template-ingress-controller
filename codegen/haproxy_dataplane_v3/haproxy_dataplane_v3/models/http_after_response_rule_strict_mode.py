from enum import Enum


class HTTPAfterResponseRuleStrictMode(str, Enum):
    OFF = "off"
    ON = "on"

    def __str__(self) -> str:
        return str(self.value)
