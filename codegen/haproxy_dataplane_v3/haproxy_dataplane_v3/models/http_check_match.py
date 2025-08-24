from enum import Enum


class HTTPCheckMatch(str, Enum):
    FHDR = "fhdr"
    HDR = "hdr"
    RSTATUS = "rstatus"
    RSTRING = "rstring"
    STATUS = "status"
    STRING = "string"

    def __str__(self) -> str:
        return str(self.value)
