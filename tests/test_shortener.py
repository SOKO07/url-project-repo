import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from shortener import Shortener  # noqa: E402


class TestShortener(unittest.TestCase):
    def setUp(self):
        self.s = Shortener()

    def test_sequential_codes(self):
        self.assertEqual(self.s.shorten("https://a.com"), "1")
        self.assertEqual(self.s.shorten("https://b.com"), "2")
        self.assertEqual(self.s.shorten("https://c.com"), "3")

    def test_same_url_same_code(self):
        a = self.s.shorten("https://a.com")
        self.assertEqual(self.s.shorten("https://a.com"), a)
        self.assertEqual(self.s.shorten("https://b.com"), "2")  # no number wasted

    def test_expand(self):
        c = self.s.shorten("https://a.com/x?y=1")
        self.assertEqual(self.s.expand(c), "https://a.com/x?y=1")

    def test_unknown_code(self):
        self.assertIsNone(self.s.expand("zzz"))
        self.assertIsNone(self.s.expand(""))

    def test_many_urls_unique_codes(self):
        codes = [self.s.shorten("https://site.com/%d" % i) for i in range(500)]
        self.assertEqual(len(codes), len(set(codes)))
        for i, c in enumerate(codes):
            self.assertEqual(self.s.expand(c), "https://site.com/%d" % i)

    def test_invalid_urls(self):
        for bad in ["", "ftp://files.example.com", "example.com", "http://a b.com",
                    "https://a.com/\nx", "https://" + "a" * 2050]:
            with self.assertRaises(ValueError, msg=repr(bad[:30])):
                self.s.shorten(bad)

    def test_non_string(self):
        with self.assertRaises(ValueError):
            self.s.shorten(None)

    def test_invalid_does_not_use_number(self):
        with self.assertRaises(ValueError):
            self.s.shorten("ftp://x")
        self.assertEqual(self.s.shorten("https://a.com"), "1")

    def test_len(self):
        self.s.shorten("https://a.com")
        self.s.shorten("https://a.com")
        self.assertEqual(len(self.s), 1)


if __name__ == "__main__":
    unittest.main()
