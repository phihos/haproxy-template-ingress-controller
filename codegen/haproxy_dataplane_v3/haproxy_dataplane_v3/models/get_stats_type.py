from enum import Enum


class GetStatsType(str, Enum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    SERVER = "server"

    def __str__(self) -> str:
        return str(self.value)
