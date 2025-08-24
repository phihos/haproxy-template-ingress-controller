from enum import Enum


class BindParamsQuicCcAlgo(str, Enum):
    BBR = "bbr"
    CUBIC = "cubic"
    NEWRENO = "newreno"
    NOCC = "nocc"

    def __str__(self) -> str:
        return str(self.value)
