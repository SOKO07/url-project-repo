import os
import re
import sys
import unittest

SRC = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, SRC)

import test_shortener  # noqa: E402
from hash_table import horner_hash  # noqa: E402
from probing_table import LinearProbingTable, TableFullError  # noqa: E402
from shortener import Shortener  # noqa: E402


def keys_for_slot(size, slot, n):
    """n distinct keys whose Horner hash is `slot` for the given table size."""
    out = []
    i = 0
    while len(out) < n:
        k = "k%d" % i
        if horner_hash(k, size) == slot:
            out.append(k)
        i += 1
    return out


class TestLinearProbingTable(unittest.TestCase):
    def test_empty(self):
        t = LinearProbingTable()
        self.assertEqual(len(t), 0)
        self.assertIsNone(t.get("a"))
        self.assertEqual(t.get("a", 5), 5)
        self.assertNotIn("a", t)

    def test_put_get_replace(self):
        t = LinearProbingTable()
        t.put("a", 1)
        t.put("b", 2)
        t.put("a", 3)
        self.assertEqual(t.get("a"), 3)
        self.assertEqual(t.get("b"), 2)
        self.assertEqual(len(t), 2)
        self.assertIn("a", t)

    def test_horner_home_slot(self):
        t = LinearProbingTable(size=11, max_load=None)
        self.assertEqual(t.slot_of("stop"), horner_hash("stop", 11))

    def test_collisions_go_to_next_slot(self):
        t = LinearProbingTable(size=11, max_load=None)
        a, b, c = keys_for_slot(11, 3, 3)
        for k in (a, b, c):
            t.put(k, k)
        self.assertEqual(t.entry_at(3).key, a)
        self.assertEqual(t.entry_at(4).key, b)
        self.assertEqual(t.entry_at(5).key, c)
        self.assertEqual(t.probes_of(a), 1)
        self.assertEqual(t.probes_of(c), 3)

    def test_wrap_around_from_last_slot(self):
        t = LinearProbingTable(size=11, max_load=None)
        a, b, c = keys_for_slot(11, 10, 3)
        for k in (a, b, c):
            t.put(k, k)
        self.assertEqual(t.entry_at(10).key, a)
        self.assertEqual(t.entry_at(0).key, b)
        self.assertEqual(t.entry_at(1).key, c)
        for k in (a, b, c):
            self.assertEqual(t.get(k), k)

    def test_full_table(self):
        t = LinearProbingTable(size=5, max_load=None)
        for i in range(5):
            t.put("key%d" % i, i)
        self.assertEqual(len(t), 5)
        self.assertEqual(t.load_factor, 1.0)
        for i in range(5):
            self.assertEqual(t.get("key%d" % i), i)
        with self.assertRaises(TableFullError):
            t.put("another", 1)
        t.put("key0", 99)  # replacing is still allowed
        self.assertEqual(t.get("key0"), 99)

    def test_miss_in_full_table_terminates(self):
        t = LinearProbingTable(size=5, max_load=None)
        for i in range(5):
            t.put("key%d" % i, i)
        value, examined = t.find("missing")
        self.assertIsNone(value)
        self.assertEqual(examined, 5)
        self.assertNotIn("missing", t)

    def test_find_counts_slots(self):
        t = LinearProbingTable(size=11, max_load=None)
        value, examined = t.find("x")
        self.assertEqual((value, examined), (None, 1))  # the empty home slot is looked at
        t.put("x", 1)
        self.assertEqual(t.find("x"), (1, 1))

    def test_grows_and_keeps_keys(self):
        t = LinearProbingTable(size=11, max_load=0.5)
        for i in range(100):
            t.put("key%d" % i, i)
        self.assertGreater(t.size, 11)
        self.assertLessEqual(t.load_factor, 0.5)
        for i in range(100):
            self.assertEqual(t.get("key%d" % i), i)

    def test_fixed_size_when_max_load_none(self):
        t = LinearProbingTable(size=101, max_load=None)
        for i in range(90):
            t.put("key%d" % i, i)
        self.assertEqual(t.size, 101)

    def test_items(self):
        t = LinearProbingTable()
        for i in range(20):
            t.put("k%d" % i, i)
        self.assertEqual(sorted(v for _, v in t.items()), list(range(20)))

    def test_no_builtin_containers_in_source(self):
        with open(os.path.join(SRC, "probing_table.py"), encoding="utf-8") as f:
            code = f.read()
        code = re.sub(r'""".*?"""', "", code, flags=re.S)
        code = re.sub(r"#.*", "", code)
        code = re.sub(r"'[^'\n]*'|\"[^\"\n]*\"", "", code)
        self.assertIsNone(re.search(r"\bdict\s*\(|\bset\s*\(|(?<![A-Za-z_])hash\s*\(|\{[^}]*\}", code))


class TestShortenerWithProbing(test_shortener.TestShortener):
    """The shortener tests again, on linear probing tables."""

    def setUp(self):
        self.s = Shortener(table_factory=LinearProbingTable)


if __name__ == "__main__":
    unittest.main()
