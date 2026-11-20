"""base62 encoding: integers <-> strings over 0-9, a-z, A-Z (in that order)."""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)


def encode(n):
    """Return the base-62 string of integer n >= 0. encode(0) == "0"."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an int")
    if n < 0:
        raise ValueError("n must be >= 0")
    if n == 0:
        return ALPHABET[0]
    digits = []
    while n > 0:
        n, r = divmod(n, BASE)
        digits.append(ALPHABET[r])
    return "".join(reversed(digits))


def decode(s):
    """Inverse of encode. Raises ValueError for empty strings or bad characters."""
    if not isinstance(s, str):
        raise TypeError("s must be a str")
    if s == "":
        raise ValueError("empty string")
    n = 0
    for ch in s:
        v = ALPHABET.find(ch)
        if v < 0:
            raise ValueError("invalid base62 character: %r" % ch)
        n = n * BASE + v
    return n
