from enum import Enum


class HTTPRequestRuleNormalizer(str, Enum):
    FRAGMENT_ENCODE = "fragment-encode"
    FRAGMENT_STRIP = "fragment-strip"
    PATH_MERGE_SLASHES = "path-merge-slashes"
    PATH_STRIP_DOT = "path-strip-dot"
    PATH_STRIP_DOTDOT = "path-strip-dotdot"
    PERCENT_DECODE_UNRESERVED = "percent-decode-unreserved"
    PERCENT_TO_UPPERCASE = "percent-to-uppercase"
    QUERY_SORT_BY_NAME = "query-sort-by-name"

    def __str__(self) -> str:
        return str(self.value)
