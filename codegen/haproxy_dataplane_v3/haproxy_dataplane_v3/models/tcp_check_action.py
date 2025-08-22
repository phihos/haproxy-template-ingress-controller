from enum import Enum


class TCPCheckAction(str, Enum):
    COMMENT = "comment"
    CONNECT = "connect"
    EXPECT = "expect"
    SEND = "send"
    SEND_BINARY = "send-binary"
    SEND_BINARY_LF = "send-binary-lf"
    SEND_LF = "send-lf"
    SET_VAR = "set-var"
    SET_VAR_FMT = "set-var-fmt"
    UNSET_VAR = "unset-var"

    def __str__(self) -> str:
        return str(self.value)
