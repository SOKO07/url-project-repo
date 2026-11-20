"""URL shortener web service (standard library http.server only).

  python src/server.py [--port 8000] [--host 0.0.0.0]
"""
import argparse
import html
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hash_table import HashTable, horner_steps  # noqa: E402
from shortener import Shortener  # noqa: E402

STYLE = """
body{font-family:system-ui,sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem;line-height:1.5}
input[type=url]{width:100%;padding:.6rem;font-size:1rem;box-sizing:border-box}
button{padding:.6rem 1.2rem;font-size:1rem;margin-top:.5rem}
.slot{display:flex;align-items:flex-start;gap:.4rem;margin:.3rem 0;flex-wrap:wrap}
.idx{width:3rem;text-align:right;font-family:monospace;padding-top:.3rem}
.node{border:1px solid #888;border-radius:6px;padding:.2rem .5rem;background:#f6f8fa;max-width:340px;word-break:break-all}
.arrow,.null{padding-top:.3rem;font-family:monospace}
table{border-collapse:collapse;font-family:monospace;font-size:.85rem}
td,th{border:1px solid #bbb;padding:.1rem .4rem}
summary{cursor:pointer}
"""


def page(title, body):
    return ("<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>%s</title><style>%s</style></head><body>%s</body></html>"
            % (html.escape(title), STYLE, body)).encode("utf-8")


def base_url(headers):
    """Public address of this server, honouring proxy headers (Codespaces)."""
    proto = headers.get("X-Forwarded-Proto")
    host = headers.get("X-Forwarded-Host") or headers.get("Host") or "localhost"
    if proto:
        proto = proto.split(",")[0].strip()
        if proto not in ("http", "https"):
            proto = "http"
    else:
        proto = "http"
    host = host.split(",")[0].strip()
    return "%s://%s" % (proto, host)


def node_html(table, node, base):
    code = node.value
    url = node.key
    link = "%s/%s" % (base, code)
    steps = horner_steps(url, table.size)
    rows = "".join(
        "<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td></tr>"
        % (html.escape(ch), c, before, after) for ch, c, before, after in steps)
    return ("<div class='node'><b>%s</b> &rarr; <a href='%s'>%s</a><br>"
            "<small>%s</small>"
            "<details><summary>Horner hash (M=%d)</summary>"
            "<table><tr><th>char</th><th>code</th><th>h before</th><th>h=(31h+c) mod M</th></tr>%s</table>"
            "</details></div>"
            % (html.escape(code), html.escape(link, quote=True), html.escape(link),
               html.escape(url), table.size, rows))


def table_page(shortener, base):
    table = shortener.by_url
    out = ["<h1>Hash table</h1><p><a href='/'>home</a> &middot; entries: %d, slots: %d, load factor: %.2f</p>"
           % (len(table), table.size, table.load_factor)]
    for i in range(table.size):
        out.append("<div class='slot'><span class='idx'>[%d]</span>" % i)
        for node in table.chain(i):
            out.append(node_html(table, node, base))
            out.append("<span class='arrow'>&rarr;</span>")
        out.append("<span class='null'>NULL</span></div>")
    return page("Hash table", "".join(out))


def make_handler(shortener):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status, body, ctype="text/html; charset=utf-8", extra=None):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            for k, v in (extra or []):
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _form(self, message=""):
            msg = "<p style='color:#c00'>%s</p>" % html.escape(message) if message else ""
            return page("URL shortener",
                        "<h1>URL shortener</h1>%s"
                        "<form method='post' action='/shorten'>"
                        "<input type='url' name='url' placeholder='https://...' required>"
                        "<button type='submit'>Shorten</button></form>"
                        "<p><a href='/table'>View hash table</a></p>" % msg)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/":
                self._send(200, self._form())
            elif path == "/table":
                self._send(200, table_page(shortener, base_url(self.headers)))
            else:
                code = path.lstrip("/")
                target = shortener.expand(code) if "/" not in code else None
                if target is None:
                    self._send(404, page("Not found", "<h1>404</h1><p>Unknown code.</p><a href='/'>home</a>"))
                else:
                    self._send(302, b"", extra=[("Location", target)])

        def do_POST(self):
            if self.path.split("?", 1)[0] != "/shorten":
                self._send(404, page("Not found", "<h1>404</h1>"))
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            raw = self.rfile.read(min(length, 8192)).decode("utf-8", "replace")
            url = (parse_qs(raw).get("url") or [""])[0].strip()
            try:
                code = shortener.shorten(url)
            except ValueError as e:
                self._send(400, self._form("Invalid URL: %s" % e))
                return
            link = "%s/%s" % (base_url(self.headers), code)
            self._send(200, page("Short link",
                                 "<h1>Short link</h1><p><a href='%s'>%s</a></p>"
                                 "<p>%s</p><p><a href='/'>another</a> &middot; <a href='/table'>table</a></p>"
                                 % (html.escape(link, quote=True), html.escape(link), html.escape(url))))

        def log_message(self, fmt, *args):
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    return Handler


def make_server(shortener, host="127.0.0.1", port=8000):
    return HTTPServer((host, port), make_handler(shortener))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    server = make_server(Shortener(HashTable), args.host, args.port)
    print("Serving on http://%s:%d (Ctrl+C to stop)" % (args.host, args.port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
