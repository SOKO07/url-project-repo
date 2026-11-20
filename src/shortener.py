"""URL shortener: serial numbers in base62, stored in our own hash tables."""

import base62
from hash_table import HashTable

MAX_URL_LENGTH = 2048


def validate_url(url):
    if not isinstance(url, str) or url == "":
        raise ValueError("url must be a non-empty string")
    if len(url) > MAX_URL_LENGTH:
        raise ValueError("url too long")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("url must start with http:// or https://")
    for ch in url:
        if ch.isspace():
            raise ValueError("url must not contain whitespace")
    if url in ("http://", "https://"):
        raise ValueError("url has no host")


class Shortener:
    def __init__(self, table_factory=HashTable):
        self.by_url = table_factory()   # url -> code
        self.by_code = table_factory()  # code -> url
        self._next = 1

    def __len__(self):
        return len(self.by_url)

    def shorten(self, url):
        validate_url(url)
        code = self.by_url.get(url)
        if code is not None:
            return code
        code = base62.encode(self._next)
        self._next += 1
        self.by_url.put(url, code)
        self.by_code.put(code, url)
        return code

    def expand(self, code):
        if not isinstance(code, str):
            return None
        return self.by_code.get(code)
