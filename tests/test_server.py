import http.client
import os
import sys
import threading
import unittest
from urllib.parse import urlencode

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from server import make_server  # noqa: E402
from shortener import Shortener  # noqa: E402


class TestServer(unittest.TestCase):
    def setUp(self):
        self.srv = make_server(Shortener(), "127.0.0.1", 0)
        self.port = self.srv.server_address[1]
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()

    def req(self, method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        c.request(method, path, body=body, headers=headers or {})
        r = c.getresponse()
        data = r.read().decode("utf-8")
        c.close()
        return r, data

    def shorten(self, url, headers=None):
        h = {"Content-Type": "application/x-www-form-urlencoded"}
        h.update(headers or {})
        return self.req("POST", "/shorten", urlencode({"url": url}), h)

    def test_index_has_form(self):
        r, body = self.req("GET", "/")
        self.assertEqual(r.status, 200)
        self.assertIn("<form", body)

    def test_shorten_and_redirect(self):
        r, body = self.shorten("https://example.com/a?b=1")
        self.assertEqual(r.status, 200)
        self.assertIn("http://127.0.0.1:%d/1" % self.port, body)
        r, _ = self.req("GET", "/1")
        self.assertEqual(r.status, 302)
        self.assertEqual(r.getheader("Location"), "https://example.com/a?b=1")

    def test_unknown_code_404(self):
        r, _ = self.req("GET", "/nope")
        self.assertEqual(r.status, 404)

    def test_bad_url_400(self):
        r, _ = self.shorten("ftp://x.com")
        self.assertEqual(r.status, 400)
        r, _ = self.shorten("")
        self.assertEqual(r.status, 400)

    def test_forwarded_headers(self):
        r, body = self.shorten("https://example.com", {
            "X-Forwarded-Host": "abc-8000.app.github.dev", "X-Forwarded-Proto": "https"})
        self.assertIn("https://abc-8000.app.github.dev/1", body)

    def test_table_page(self):
        self.shorten("https://example.com/x")
        r, body = self.req("GET", "/table")
        self.assertEqual(r.status, 200)
        self.assertIn("https://example.com/x", body)
        self.assertIn("NULL", body)
        self.assertIn("Horner", body)


if __name__ == "__main__":
    unittest.main()
