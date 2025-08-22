from enum import Enum


class CompressionAlgosResItem(str, Enum):
    DEFLATE = "deflate"
    GZIP = "gzip"
    IDENTITY = "identity"
    RAW_DEFLATE = "raw-deflate"

    def __str__(self) -> str:
        return str(self.value)
