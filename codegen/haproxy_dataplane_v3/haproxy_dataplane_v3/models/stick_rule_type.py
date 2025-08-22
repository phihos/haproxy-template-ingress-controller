from enum import Enum


class StickRuleType(str, Enum):
    MATCH = "match"
    ON = "on"
    STORE_REQUEST = "store-request"
    STORE_RESPONSE = "store-response"

    def __str__(self) -> str:
        return str(self.value)
