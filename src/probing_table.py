"""Hash table with open addressing and linear probing.

Same interface as HashTable (put, get, find, len, in, load_factor).
No dict, set or built-in hash(); the Horner hash is reused.
Deletion is not supported (not needed by the shortener).
"""
from hash_table import horner_hash


class Entry:
    def __init__(self, key, value):
        self.key = key
        self.value = value


class TableFullError(Exception):
    """Raised when a new key is put into a table with no free slot."""


class LinearProbingTable:
    def __init__(self, size=11, max_load=0.75):
        if size < 1:
            raise ValueError("size must be >= 1")
        self.size = size
        self.max_load = max_load
        self._slots = [None] * size
        self._count = 0

    def __len__(self):
        return self._count

    @property
    def load_factor(self):
        return self._count / self.size

    def slot_of(self, key):
        """Home slot: the Horner hash of the key."""
        return horner_hash(key, self.size)

    def _locate(self, key):
        """Return (index or None, slots examined). Stops at the key, an empty slot, or a full lap."""
        i = self.slot_of(key)
        examined = 0
        while examined < self.size:
            examined += 1
            entry = self._slots[i]
            if entry is None:
                return None, examined
            if entry.key == key:
                return i, examined
            i = (i + 1) % self.size  # wraps from the last slot to slot 0
        return None, examined

    def find(self, key):
        """Return (value or None, number of slots examined)."""
        i, examined = self._locate(key)
        if i is None:
            return None, examined
        return self._slots[i].value, examined

    def get(self, key, default=None):
        i, _ = self._locate(key)
        if i is None:
            return default
        return self._slots[i].value

    def __contains__(self, key):
        i, _ = self._locate(key)
        return i is not None

    def put(self, key, value):
        i, _ = self._locate(key)
        if i is not None:
            self._slots[i].value = value
            return
        if self._count >= self.size:
            raise TableFullError("table is full")
        j = self.slot_of(key)
        while self._slots[j] is not None:
            j = (j + 1) % self.size
        self._slots[j] = Entry(key, value)
        self._count += 1
        if self.max_load is not None and self.load_factor > self.max_load:
            self._grow()

    def _grow(self):
        old = self._slots
        self.size = 2 * self.size + 1
        self._slots = [None] * self.size
        self._count = 0
        for entry in old:
            if entry is not None:
                self.put(entry.key, entry.value)

    def entry_at(self, slot):
        return self._slots[slot]

    def probes_of(self, key):
        """Slots examined to find a stored key (1 = found in its home slot)."""
        i, examined = self._locate(key)
        return examined if i is not None else 0

    def items(self):
        for entry in self._slots:
            if entry is not None:
                yield entry.key, entry.value
