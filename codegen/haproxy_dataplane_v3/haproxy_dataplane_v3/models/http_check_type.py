from enum import Enum


class HTTPCheckType(str, Enum):
    COMMENT = "comment"
    CONNECT = "connect"
    DISABLE_ON_404 = "disable-on-404"
    EXPECT = "expect"
    SEND = "send"
    SEND_STATE = "send-state"
    SET_VAR = "set-var"
    SET_VAR_FMT = "set-var-fmt"
    UNSET_VAR = "unset-var"

    def __str__(self) -> str:
        return str(self.value)
