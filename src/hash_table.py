"""Hash table with separate chaining and a Horner hash.

No dict, set or built-in hash() is used: slots are a list of linked lists.
"""

MULT = 31


class Node:
    def __init__(self, key, value, next_node=None):
        self.key = key
        self.value = value
        self.next = next_node


def horner_steps(key, m):
    """Return [(char, code, h_before, h_after), ...] for h = (31*h + c) mod m."""
    steps = []
    h = 0
    for ch in key:
        before = h
        h = (MULT * h + ord(ch)) % m
        steps.append((ch, ord(ch), before, h))
    return steps


def horner_hash(key, m):
    h = 0
    for ch in key:
        h = (MULT * h + ord(ch)) % m
    return h


class HashTable:
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
        return horner_hash(key, self.size)

    def find(self, key):
        """Return (value or None, number of nodes compared)."""
        node = self._slots[self.slot_of(key)]
        compared = 0
        while node is not None:
            compared += 1
            if node.key == key:
                return node.value, compared
            node = node.next
        return None, compared

    def get(self, key, default=None):
        node = self._slots[self.slot_of(key)]
        while node is not None:
            if node.key == key:
                return node.value
            node = node.next
        return default

    def __contains__(self, key):
        node = self._slots[self.slot_of(key)]
        while node is not None:
            if node.key == key:
                return True
            node = node.next
        return False

    def put(self, key, value):
        i = self.slot_of(key)
        node = self._slots[i]
        while node is not None:
            if node.key == key:
                node.value = value
                return
            node = node.next
        # new node goes to the end of the chain so insertion order is visible
        new = Node(key, value)
        if self._slots[i] is None:
            self._slots[i] = new
        else:
            tail = self._slots[i]
            while tail.next is not None:
                tail = tail.next
            tail.next = new
        self._count += 1
        if self.max_load is not None and self.load_factor > self.max_load:
            self._grow()

    def _grow(self):
        old = self._slots
        self.size = 2 * self.size + 1
        self._slots = [None] * self.size
        self._count = 0
        for head in old:
            node = head
            while node is not None:
                self.put(node.key, node.value)
                node = node.next

    def chain(self, slot):
        """Yield the nodes of one slot, front to back."""
        node = self._slots[slot]
        while node is not None:
            yield node
            node = node.next

    def items(self):
        for i in range(self.size):
            for node in self.chain(i):
                yield node.key, node.value
