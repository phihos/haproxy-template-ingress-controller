from enum import Enum


class LogTargetFacility(str, Enum):
    ALERT = "alert"
    AUDIT = "audit"
    AUTH = "auth"
    AUTH2 = "auth2"
    CRON = "cron"
    CRON2 = "cron2"
    DAEMON = "daemon"
    FTP = "ftp"
    KERN = "kern"
    LOCAL0 = "local0"
    LOCAL1 = "local1"
    LOCAL2 = "local2"
    LOCAL3 = "local3"
    LOCAL4 = "local4"
    LOCAL5 = "local5"
    LOCAL6 = "local6"
    LOCAL7 = "local7"
    LPR = "lpr"
    MAIL = "mail"
    NEWS = "news"
    NTP = "ntp"
    SYSLOG = "syslog"
    USER = "user"
    UUCP = "uucp"

    def __str__(self) -> str:
        return str(self.value)
