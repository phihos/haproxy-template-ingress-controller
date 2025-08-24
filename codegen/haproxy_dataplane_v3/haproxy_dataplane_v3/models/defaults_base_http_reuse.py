from enum import Enum


class DefaultsBaseHttpReuse(str, Enum):
    AGGRESSIVE = "aggressive"
    ALWAYS = "always"
    NEVER = "never"
    SAFE = "safe"

    def __str__(self) -> str:
        return str(self.value)
