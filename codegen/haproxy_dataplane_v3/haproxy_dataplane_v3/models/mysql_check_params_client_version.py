from enum import Enum


class MysqlCheckParamsClientVersion(str, Enum):
    POST_41 = "post-41"
    PRE_41 = "pre-41"

    def __str__(self) -> str:
        return str(self.value)
