from enum import Enum


class ACMEProviderKeytype(str, Enum):
    ECDSA = "ECDSA"
    RSA = "RSA"

    def __str__(self) -> str:
        return str(self.value)
