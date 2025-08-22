from enum import Enum


class SSLFrontendUseCertificateSslMinVer(str, Enum):
    SSLV3 = "SSLv3"
    TLSV1_0 = "TLSv1.0"
    TLSV1_1 = "TLSv1.1"
    TLSV1_2 = "TLSv1.2"
    TLSV1_3 = "TLSv1.3"

    def __str__(self) -> str:
        return str(self.value)
