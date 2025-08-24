from enum import Enum


class FilterType(str, Enum):
    BWLIM_IN = "bwlim-in"
    BWLIM_OUT = "bwlim-out"
    CACHE = "cache"
    COMPRESSION = "compression"
    FCGI_APP = "fcgi-app"
    SPOE = "spoe"
    TRACE = "trace"

    def __str__(self) -> str:
        return str(self.value)
