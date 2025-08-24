from enum import Enum


class ClusterSettingsClusterControllerInformationLogTargetsItemProtocol(str, Enum):
    TCP = "tcp"
    UDP = "udp"

    def __str__(self) -> str:
        return str(self.value)
