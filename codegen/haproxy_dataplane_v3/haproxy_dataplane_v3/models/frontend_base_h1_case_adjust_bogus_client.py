from enum import Enum


class FrontendBaseH1CaseAdjustBogusClient(str, Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"

    def __str__(self) -> str:
        return str(self.value)
