import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from base62 import encode, decode  # noqa: E402


class TestBase62(unittest.TestCase):
    def test_zero_is_char_zero(self):
        self.assertEqual(encode(0), "0")

    def test_known_values(self):
        self.assertEqual(encode(9), "9")
        self.assertEqual(encode(10), "a")
        self.assertEqual(encode(35), "z")
        self.assertEqual(encode(36), "A")
        self.assertEqual(encode(61), "Z")
        self.assertEqual(encode(62), "10")
        self.assertEqual(encode(3844), "100")

    def test_roundtrip(self):
        for n in list(range(0, 5000)) + [10**9, 2**64]:
            self.assertEqual(decode(encode(n)), n)

    def test_decode_known(self):
        self.assertEqual(decode("0"), 0)
        self.assertEqual(decode("100"), 3844)

    def test_negative_rejected(self):
        with self.assertRaises(ValueError):
            encode(-1)

    def test_bad_decode(self):
        for bad in ["", "a-b", " ", "가"]:
            with self.assertRaises(ValueError):
                decode(bad)

    def test_type_errors(self):
        with self.assertRaises(TypeError):
            encode("1")
        with self.assertRaises(TypeError):
            encode(True)
        with self.assertRaises(TypeError):
            decode(5)


if __name__ == "__main__":
    unittest.main()
