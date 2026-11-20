import glob
import os
import re
import sys
import unittest

SRC = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, SRC)

from hash_table import HashTable  # noqa: E402


def horner(key, m):
    h = 0
    for c in key:
        h = (31 * h + ord(c)) % m
    return h


class TestHashTable(unittest.TestCase):
    def test_empty(self):
        t = HashTable()
        self.assertEqual(len(t), 0)
        self.assertIsNone(t.get("a"))
        self.assertEqual(t.get("a", 5), 5)
        self.assertNotIn("a", t)

    def test_put_get(self):
        t = HashTable()
        t.put("a", 1)
        t.put("b", 2)
        self.assertEqual(t.get("a"), 1)
        self.assertEqual(t.get("b"), 2)
        self.assertEqual(len(t), 2)
        self.assertIn("a", t)

    def test_same_key_replaces(self):
        t = HashTable()
        t.put("a", 1)
        t.put("a", 2)
        self.assertEqual(t.get("a"), 2)
        self.assertEqual(len(t), 1)

    def test_horner_slot(self):
        t = HashTable(size=11, max_load=None)
        self.assertEqual(t.slot_of("stop"), horner("stop", 11))
        self.assertEqual(t.size, 11)

    def test_colliding_keys_all_found(self):
        t = HashTable(size=11, max_load=None)
        keys = ["k%d" % i for i in range(200)]
        for i, k in enumerate(keys):
            t.put(k, i)
        slots = set(t.slot_of(k) for k in keys)
        self.assertLess(len(slots), 200)  # collisions certainly happened
        for i, k in enumerate(keys):
            self.assertEqual(t.get(k), i)
        self.assertEqual(len(t), 200)

    def test_find_counts_nodes(self):
        t = HashTable(size=11, max_load=None)
        value, compared = t.find("x")
        self.assertIsNone(value)
        self.assertEqual(compared, 0)  # empty slot compares nothing
        t.put("x", 1)
        value, compared = t.find("x")
        self.assertEqual((value, compared), (1, 1))

    def test_find_miss_counts_chain_length(self):
        t = HashTable(size=1, max_load=None)
        for k in ["a", "b", "c"]:
            t.put(k, k)
        value, compared = t.find("zzz")
        self.assertIsNone(value)
        self.assertEqual(compared, 3)

    def test_grows_and_keeps_keys(self):
        t = HashTable(size=11, max_load=0.75)
        for i in range(100):
            t.put("key%d" % i, i)
        self.assertGreater(t.size, 11)
        self.assertLessEqual(t.load_factor, 0.75)
        for i in range(100):
            self.assertEqual(t.get("key%d" % i), i)

    def test_no_growth_when_max_load_none(self):
        t = HashTable(size=11, max_load=None)
        for i in range(100):
            t.put("key%d" % i, i)
        self.assertEqual(t.size, 11)
        self.assertAlmostEqual(t.load_factor, 100 / 11)

    def test_items_cover_all(self):
        t = HashTable()
        for i in range(20):
            t.put("k%d" % i, i)
        self.assertEqual(sorted(v for _, v in t.items()), list(range(20)))

    def test_no_builtin_containers_in_src(self):
        pattern = re.compile(r"\bdict\s*\(|\bset\s*\(|\bhash\s*\(|\{\s*\}|\{[^}]*:[^}]*\}")
        for path in glob.glob(os.path.join(SRC, "hash_table.py")):
            with open(path, encoding="utf-8") as f:
                code = f.read()
            code = re.sub(r'""".*?"""', "", code, flags=re.S)
            code = re.sub(r"#.*", "", code)
            code = re.sub(r"'[^'\n]*'|\"[^\"\n]*\"", "", code)
            self.assertIsNone(pattern.search(code), path)


if __name__ == "__main__":
    unittest.main()
