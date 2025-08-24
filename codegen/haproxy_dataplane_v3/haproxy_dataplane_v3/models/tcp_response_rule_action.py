from enum import Enum


class TCPResponseRuleAction(str, Enum):
    ACCEPT = "accept"
    CLOSE = "close"
    DO_LOG = "do-log"
    LUA = "lua"
    REJECT = "reject"
    SC_ADD_GPC = "sc-add-gpc"
    SC_INC_GPC = "sc-inc-gpc"
    SC_INC_GPC0 = "sc-inc-gpc0"
    SC_INC_GPC1 = "sc-inc-gpc1"
    SC_SET_GPT = "sc-set-gpt"
    SC_SET_GPT0 = "sc-set-gpt0"
    SEND_SPOE_GROUP = "send-spoe-group"
    SET_BANDWIDTH_LIMIT = "set-bandwidth-limit"
    SET_FC_MARK = "set-fc-mark"
    SET_FC_TOS = "set-fc-tos"
    SET_LOG_LEVEL = "set-log-level"
    SET_MARK = "set-mark"
    SET_NICE = "set-nice"
    SET_TOS = "set-tos"
    SET_VAR = "set-var"
    SET_VAR_FMT = "set-var-fmt"
    SILENT_DROP = "silent-drop"
    UNSET_VAR = "unset-var"

    def __str__(self) -> str:
        return str(self.value)
