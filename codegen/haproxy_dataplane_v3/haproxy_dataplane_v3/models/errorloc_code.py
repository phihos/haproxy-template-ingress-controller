from enum import IntEnum


class ErrorlocCode(IntEnum):
    VALUE_200 = 200
    VALUE_400 = 400
    VALUE_401 = 401
    VALUE_403 = 403
    VALUE_404 = 404
    VALUE_405 = 405
    VALUE_407 = 407
    VALUE_408 = 408
    VALUE_410 = 410
    VALUE_413 = 413
    VALUE_425 = 425
    VALUE_429 = 429
    VALUE_500 = 500
    VALUE_501 = 501
    VALUE_502 = 502
    VALUE_503 = 503
    VALUE_504 = 504

    def __str__(self) -> str:
        return str(self.value)
