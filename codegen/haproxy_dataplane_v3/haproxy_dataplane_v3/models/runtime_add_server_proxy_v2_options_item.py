from enum import Enum


class RuntimeAddServerProxyV2OptionsItem(str, Enum):
    AUTHORITY = "authority"
    CERT_CN = "cert-cn"
    CERT_KEY = "cert-key"
    CERT_SIG = "cert-sig"
    CRC32C = "crc32c"
    SSL = "ssl"
    SSL_CIPHER = "ssl-cipher"
    UNIQUE_ID = "unique-id"

    def __str__(self) -> str:
        return str(self.value)
