from enum import Enum


class HTTPAfterResponseRuleLogLevel(str, Enum):
    ALERT = "alert"
    CRIT = "crit"
    DEBUG = "debug"
    EMERG = "emerg"
    ERR = "err"
    INFO = "info"
    NOTICE = "notice"
    SILENT = "silent"
    WARNING = "warning"

    def __str__(self) -> str:
        return str(self.value)
