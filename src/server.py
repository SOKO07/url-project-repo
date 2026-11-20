"""URL shortener web service (standard library http.server only).

  python src/server.py [--port 8000] [--host 0.0.0.0] [--table chaining|probing]
"""
import argparse
import html
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hash_table import HashTable, horner_steps  # noqa: E402
from probing_table import LinearProbingTable  # noqa: E402
from shortener import Shortener  # noqa: E402

STYLE = """
:root{--bg:#f4f6fb;--card:#fff;--text:#1d2433;--muted:#6b7385;--line:#e2e6f0;--accent:#4f6df5;--accent2:#8a5cf6;--warn:#f59e0b;--bad:#d93f3f;--code:#f0f3fa}
@media (prefers-color-scheme:dark){:root{--bg:#10131c;--card:#181c28;--text:#e8ebf4;--muted:#98a0b5;--line:#2a3042;--code:#202637}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,"Segoe UI","Noto Sans KR",sans-serif;line-height:1.55}
.wrap{max-width:900px;margin:0 auto;padding:0 1rem 3rem}
header.bar{background:linear-gradient(120deg,var(--accent),var(--accent2));color:#fff;padding:1.1rem 0;margin-bottom:2rem}
header.bar .wrap{display:flex;align-items:center;justify-content:space-between;padding-bottom:0}
header.bar a{color:#fff;text-decoration:none}
.brand{font-weight:800;font-size:1.2rem;letter-spacing:-.02em}
nav a{margin-left:1rem;opacity:.9;font-weight:600}
nav a:hover{opacity:1;text-decoration:underline}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:1.6rem;box-shadow:0 6px 24px rgba(30,40,80,.06)}
h1{margin:.2rem 0 .4rem;font-size:1.7rem;letter-spacing:-.02em}
p.lead{color:var(--muted);margin:.2rem 0 1.2rem}
form.shorten{display:flex;gap:.6rem;flex-wrap:wrap}
form.shorten input{flex:1;min-width:220px;padding:.85rem 1rem;font-size:1rem;border:2px solid var(--line);border-radius:12px;background:var(--card);color:var(--text);outline:none}
form.shorten input:focus{border-color:var(--accent)}
.btn{padding:.85rem 1.4rem;font-size:1rem;font-weight:700;border:0;border-radius:12px;background:linear-gradient(120deg,var(--accent),var(--accent2));color:#fff;cursor:pointer;text-decoration:none;display:inline-block}
.btn:hover{filter:brightness(1.08)}
.btn.ghost{background:var(--code);color:var(--text)}
.error{background:rgba(217,63,63,.1);border:1px solid var(--bad);color:var(--bad);padding:.7rem 1rem;border-radius:10px;margin-bottom:1rem}
.result{display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;background:var(--code);border-radius:12px;padding:.9rem 1rem;margin:1rem 0}
.result a.short{font-size:1.35rem;font-weight:800;color:var(--accent);text-decoration:none;word-break:break-all}
.orig{color:var(--muted);word-break:break-all;font-size:.92rem}
.chips{display:flex;gap:.5rem;flex-wrap:wrap;margin:.8rem 0 1.2rem}
.chip{background:var(--code);border-radius:999px;padding:.25rem .8rem;font-size:.85rem;color:var(--muted)}
.chip b{color:var(--text)}
.actions{display:flex;gap:.6rem;margin-top:1.2rem;flex-wrap:wrap}
.slot{display:flex;align-items:flex-start;gap:.5rem;margin:.35rem 0;flex-wrap:wrap}
.slot.empty{opacity:.55}
.slot.collide .idx{background:var(--warn);color:#1d2433}
.idx{min-width:2.6rem;text-align:center;font-family:ui-monospace,Consolas,monospace;font-weight:700;background:var(--accent);color:#fff;border-radius:8px;padding:.25rem .4rem;margin-top:.2rem}
.slot.empty .idx{background:var(--line);color:var(--muted)}
.node{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--accent2);border-radius:10px;padding:.45rem .7rem;max-width:360px;word-break:break-all;box-shadow:0 2px 8px rgba(30,40,80,.05)}
.node a{color:var(--accent);font-weight:700;text-decoration:none}
.node small{color:var(--muted)}
.node .meta{color:var(--muted);font-size:.82rem}
.arrow{color:var(--accent);font-weight:800;padding-top:.5rem}
.null{color:var(--muted);font-family:ui-monospace,Consolas,monospace;font-size:.85rem;padding-top:.5rem}
table{border-collapse:collapse;font-family:ui-monospace,Consolas,monospace;font-size:.8rem;margin-top:.4rem}
td,th{border:1px solid var(--line);padding:.1rem .45rem;text-align:right}
th{background:var(--code)}
summary{cursor:pointer;color:var(--accent);font-size:.85rem;font-weight:600}
footer{text-align:center;color:var(--muted);font-size:.85rem;margin-top:2rem}
"""

COPY_JS = """<script>
function copyLink(btn){var el=document.getElementById('short');var t=el.textContent;
function fallback(){var r=document.createRange();r.selectNode(el);var s=getSelection();s.removeAllRanges();s.addRange(r);btn.textContent='선택됨 (Ctrl+C)'}
if(navigator.clipboard){navigator.clipboard.writeText(t).then(function(){btn.textContent='복사됨!'},fallback)}else{fallback()}}
</script>"""


def page(title, body):
    return ("<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>%s</title><style>%s</style></head><body>"
            "<header class='bar'><div class='wrap'><a class='brand' href='/'>&#128279; 짧은주소</a>"
            "<nav><a href='/'>홈</a><a href='/table'>해시 테이블</a></nav></div></header>"
            "<div class='wrap'>%s<footer>고급알고리즘 과제2 &middot; 직접 만든 해시 테이블 위에서 동작합니다</footer></div>"
            "</body></html>"
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


def horner_table(key, size):
    rows = "".join(
        "<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td></tr>"
        % (html.escape(ch), c, before, after) for ch, c, before, after in horner_steps(key, size))
    return ("<details><summary>Horner hash 계산 (M=%d)</summary>"
            "<table><tr><th>char</th><th>code</th><th>h before</th><th>h=(31h+c) mod M</th></tr>%s</table>"
            "</details>" % (size, rows))


def node_html(table, node, base):
    link = "%s/%s" % (base, node.value)
    return ("<div class='node'><b>%s</b> &rarr; <a href='%s'>%s</a><br><small>%s</small>%s</div>"
            % (html.escape(node.value), html.escape(link, quote=True), html.escape(link),
               html.escape(node.key), horner_table(node.key, table.size)))


def probing_row(table, i, base):
    entry = table.entry_at(i)
    if entry is None:
        return "<div class='slot empty'><span class='idx'>%d</span><span class='null'>(empty)</span></div>" % i
    home = table.slot_of(entry.key)
    probes = table.probes_of(entry.key)
    link = "%s/%s" % (base, entry.value)
    return ("<div class='slot%s'><span class='idx'>%d</span><div class='node'><b>%s</b> &rarr; "
            "<a href='%s'>%s</a><br><small>%s</small><br>"
            "<span class='meta'>home slot %d, probed %d slot(s)%s</span>%s</div></div>"
            % (" collide" if probes > 1 else "", i, html.escape(entry.value),
               html.escape(link, quote=True), html.escape(link), html.escape(entry.key),
               home, probes, " (wrapped around)" if i < home else "",
               horner_table(entry.key, table.size)))


def stats_chips(table):
    return ("<div class='chips'><span class='chip'>항목 <b>%d</b></span>"
            "<span class='chip'>슬롯 <b>%d</b></span>"
            "<span class='chip'>load factor <b>%.2f</b></span></div>"
            % (len(table), table.size, table.load_factor))


def table_page(shortener, base):
    table = shortener.by_url
    if isinstance(table, LinearProbingTable):
        out = ["<div class='card'><h1>해시 테이블 (linear probing)</h1>"
               "<p class='lead'>슬롯 하나에 키 하나. 주황 번호는 홈 슬롯에서 밀려난 키입니다.</p>%s"
               % stats_chips(table)]
        for i in range(table.size):
            out.append(probing_row(table, i, base))
        out.append("</div>")
        return page("Hash table", "".join(out))
    out = ["<div class='card'><h1>해시 테이블 (분리 연쇄)</h1>"
           "<p class='lead'>같은 슬롯에 들어간 URL은 연결 리스트로 이어집니다. 주황 번호는 충돌한 슬롯입니다.</p>%s"
           % stats_chips(table)]
    for i in range(table.size):
        nodes = list(table.chain(i))
        cls = "slot" + (" collide" if len(nodes) > 1 else "") + ("" if nodes else " empty")
        out.append("<div class='%s'><span class='idx'>%d</span>" % (cls, i))
        for node in nodes:
            out.append(node_html(table, node, base))
            out.append("<span class='arrow'>&rarr;</span>")
        out.append("<span class='null'>NULL</span></div>")
    out.append("</div>")
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
            msg = "<div class='error'>%s</div>" % html.escape(message) if message else ""
            return page("URL shortener",
                        "<div class='card'><h1>긴 주소를 짧게</h1>"
                        "<p class='lead'>주소를 붙여 넣으면 짧은 링크를 만들어 줍니다.</p>%s"
                        "<form class='shorten' method='post' action='/shorten'>"
                        "<input type='url' name='url' placeholder='https://...' required autofocus>"
                        "<button class='btn' type='submit'>Shorten</button></form>"
                        "<div class='actions'><a class='btn ghost' href='/table'>해시 테이블 보기</a></div></div>"
                        % msg)

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
                    self._send(404, page("Not found",
                                         "<div class='card'><h1>404</h1>"
                                         "<p class='lead'>없는 코드입니다 (Unknown code).</p>"
                                         "<a class='btn' href='/'>홈으로</a></div>"))
                else:
                    self._send(302, b"", extra=[("Location", target)])

        def do_POST(self):
            if self.path.split("?", 1)[0] != "/shorten":
                self._send(404, page("Not found", "<div class='card'><h1>404</h1></div>"))
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
                self._send(400, self._form("주소가 올바르지 않습니다: %s" % e))
                return
            link = "%s/%s" % (base_url(self.headers), code)
            self._send(200, page("Short link",
                                 "<div class='card'><h1>짧은 링크가 만들어졌어요</h1>"
                                 "<div class='result'><a class='short' id='short' href='%s'>%s</a>"
                                 "<button class='btn' type='button' onclick='copyLink(this)'>복사</button></div>"
                                 "<div class='orig'>원래 주소: %s</div>"
                                 "<div class='actions'><a class='btn' href='/'>하나 더 만들기</a>"
                                 "<a class='btn ghost' href='/table'>해시 테이블 보기</a></div></div>%s"
                                 % (html.escape(link, quote=True), html.escape(link),
                                    html.escape(url), COPY_JS)))

        def log_message(self, fmt, *args):
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    return Handler


def make_server(shortener, host="127.0.0.1", port=8000):
    return HTTPServer((host, port), make_handler(shortener))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--table", choices=["chaining", "probing"], default="chaining")
    args = ap.parse_args()
    factory = LinearProbingTable if args.table == "probing" else HashTable
    server = make_server(Shortener(factory), args.host, args.port)
    print("Serving on http://%s:%d (Ctrl+C to stop)" % (args.host, args.port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
