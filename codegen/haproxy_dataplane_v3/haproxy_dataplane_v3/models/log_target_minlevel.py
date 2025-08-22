from enum import Enum


class LogTargetMinlevel(str, Enum):
    ALERT = "alert"
    CRIT = "crit"
    DEBUG = "debug"
    EMERG = "emerg"
    ERR = "err"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"

    def __str__(self) -> str:
        return str(self.value)
