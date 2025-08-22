from enum import Enum


class BackendBaseAdvCheck(str, Enum):
    HTTPCHK = "httpchk"
    LDAP_CHECK = "ldap-check"
    MYSQL_CHECK = "mysql-check"
    PGSQL_CHECK = "pgsql-check"
    REDIS_CHECK = "redis-check"
    SMTPCHK = "smtpchk"
    SSL_HELLO_CHK = "ssl-hello-chk"
    TCP_CHECK = "tcp-check"

    def __str__(self) -> str:
        return str(self.value)
