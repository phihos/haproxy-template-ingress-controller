from enum import Enum


class BindParamsLevel(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    USER = "user"

    def __str__(self) -> str:
        return str(self.value)
