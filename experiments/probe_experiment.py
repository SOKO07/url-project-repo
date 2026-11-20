"""Chaining: average nodes compared vs load factor (hit/miss) against theory.

Run:  python experiments/probe_experiment.py
Writes experiments/results.csv and experiments/chart.svg.
"""
import csv
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))

from hash_table import HashTable  # noqa: E402

M = 4093
LOADS = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]
MISSES = 2000
HITS = 2000
SEED = 2026


def random_url(rng, tag):
    path = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(12))
    return "https://%s.example.com/%s/%s" % (tag, path, rng.randrange(10**6))


def measure(alpha, rng):
    n = int(round(alpha * M))
    t = HashTable(size=M, max_load=None)
    keys = []
    for i in range(n):
        k = random_url(rng, "in") + "/%d" % i
        keys.append(k)
        t.put(k, i)
    hit_total = 0
    for _ in range(HITS):
        value, compared = t.find(rng.choice(keys))
        hit_total += compared
    miss_total = 0
    for i in range(MISSES):
        value, compared = t.find(random_url(rng, "out") + "/m%d" % i)
        miss_total += compared
    return hit_total / HITS, miss_total / MISSES


def write_svg(rows, path):
    w, h, left, bottom, top, right = 640, 420, 60, 50, 40, 20
    xmax, ymax = 4.0, 4.5

    def sx(x):
        return left + (w - left - right) * x / xmax

    def sy(y):
        return h - bottom - (h - bottom - top) * y / ymax

    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" font-family="sans-serif" font-size="12">' % (w, h),
           '<rect width="100%" height="100%" fill="white"/>',
           '<text x="%d" y="22" font-size="14" font-weight="bold">Separate chaining: nodes compared vs load factor (M=%d)</text>' % (left, M)]
    for g in range(0, 5):
        out.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#ddd"/>' % (left, sy(g), w - right, sy(g)))
        out.append('<text x="%d" y="%.1f" text-anchor="end">%d</text>' % (left - 6, sy(g) + 4, g))
    for g in range(0, 5):
        out.append('<text x="%.1f" y="%d" text-anchor="middle">%d</text>' % (sx(g), h - bottom + 18, g))
    out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="black"/>' % (left, h - bottom, w - right, h - bottom))
    out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="black"/>' % (left, top, left, h - bottom))
    out.append('<text x="%d" y="%d" text-anchor="middle">load factor (n / M)</text>' % ((left + w - right) // 2, h - 10))
    out.append('<text transform="translate(16,%d) rotate(-90)" text-anchor="middle">average nodes compared</text>' % ((top + h - bottom) // 2))
    series = [("hit (measured)", 1, "#1f77b4", "", True), ("hit (theory 1+a/2)", 3, "#1f77b4", "6,4", False),
              ("miss (measured)", 2, "#d62728", "", True), ("miss (theory a)", 4, "#d62728", "6,4", False)]
    for name, col, color, dash, dots in series:
        pts = " ".join("%.1f,%.1f" % (sx(float(r[0])), sy(float(r[col]))) for r in rows)
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2"%s/>' % (pts, color, d))
        if dots:
            for r in rows:
                out.append('<circle cx="%.1f" cy="%.1f" r="3.5" fill="%s"/>' % (sx(float(r[0])), sy(float(r[col])), color))
    ly = top + 8
    for i, (name, col, color, dash, dots) in enumerate(series):
        y = ly + 18 * i
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2"%s/>' % (left + 14, y, left + 44, y, color, d))
        out.append('<text x="%d" y="%d">%s</text>' % (left + 50, y + 4, name))
    out.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))


def main():
    rng = random.Random(SEED)
    rows = []
    print("%6s %12s %12s %12s %12s" % ("alpha", "hit", "miss", "hit theory", "miss theory"))
    for alpha in LOADS:
        hit, miss = measure(alpha, rng)
        row = (alpha, round(hit, 4), round(miss, 4), round(1 + alpha / 2, 4), round(alpha, 4))
        rows.append(row)
        print("%6.2f %12.3f %12.3f %12.3f %12.3f" % row)
    with open(os.path.join(HERE, "results.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["load_factor", "hit_measured", "miss_measured", "hit_theory", "miss_theory"])
        wr.writerows(rows)
    write_svg(rows, os.path.join(HERE, "chart.svg"))


if __name__ == "__main__":
    main()
