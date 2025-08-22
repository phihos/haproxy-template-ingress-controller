from enum import Enum


class HTTPAfterResponseRuleType(str, Enum):
    ADD_HEADER = "add-header"
    ALLOW = "allow"
    CAPTURE = "capture"
    DEL_ACL = "del-acl"
    DEL_HEADER = "del-header"
    DEL_MAP = "del-map"
    DO_LOG = "do-log"
    REPLACE_HEADER = "replace-header"
    REPLACE_VALUE = "replace-value"
    SC_ADD_GPC = "sc-add-gpc"
    SC_INC_GPC = "sc-inc-gpc"
    SC_INC_GPC0 = "sc-inc-gpc0"
    SC_INC_GPC1 = "sc-inc-gpc1"
    SC_SET_GPT = "sc-set-gpt"
    SC_SET_GPT0 = "sc-set-gpt0"
    SET_HEADER = "set-header"
    SET_LOG_LEVEL = "set-log-level"
    SET_MAP = "set-map"
    SET_STATUS = "set-status"
    SET_VAR = "set-var"
    SET_VAR_FMT = "set-var-fmt"
    STRICT_MODE = "strict-mode"
    UNSET_VAR = "unset-var"

    def __str__(self) -> str:
        return str(self.value)
