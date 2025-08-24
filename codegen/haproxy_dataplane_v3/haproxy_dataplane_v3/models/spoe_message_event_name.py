from enum import Enum


class SPOEMessageEventName(str, Enum):
    ON_BACKEND_HTTP_REQUEST = "on-backend-http-request"
    ON_BACKEND_TCP_REQUEST = "on-backend-tcp-request"
    ON_CLIENT_SESSION = "on-client-session"
    ON_FRONTEND_HTTP_REQUEST = "on-frontend-http-request"
    ON_FRONTEND_TCP_REQUEST = "on-frontend-tcp-request"
    ON_HTTP_RESPONSE = "on-http-response"
    ON_SERVER_SESSION = "on-server-session"
    ON_TCP_RESPONSE = "on-tcp-response"

    def __str__(self) -> str:
        return str(self.value)
