"""Separate chaining vs linear probing: hit/miss cost against load factor.

Same keys, same size (M=4093), no resizing. Cost = nodes compared (chaining)
or slots examined (linear probing). Theory (Topic 08):
  chaining : hit 1 + a/2         miss a
  probing  : hit (1 + 1/(1-a))/2 miss (1 + 1/(1-a)^2)/2

Run:  python experiments/compare_experiment.py
Writes experiments/compare_results.csv and experiments/compare_chart.svg.
"""
import csv
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))

from hash_table import HashTable  # noqa: E402
from probing_table import LinearProbingTable  # noqa: E402

M = 4093
LOADS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
QUERIES = 2000
REPEATS = 5
SEED = 2026


def random_url(rng, tag, i):
    path = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(12))
    return "https://%s.example.com/%s/%d" % (tag, path, i)


def cost(table, probes):
    total = 0
    for k in probes:
        value, c = table.find(k)
        total += c
    return total / len(probes)


def run_once(alpha, rng):
    n = int(round(alpha * M))
    keys = [random_url(rng, "in", i) for i in range(n)]
    chain = HashTable(size=M, max_load=None)
    probe = LinearProbingTable(size=M, max_load=None)
    for i, k in enumerate(keys):
        chain.put(k, i)
        probe.put(k, i)
    hits = [rng.choice(keys) for _ in range(QUERIES)]
    misses = [random_url(rng, "out", i) for i in range(QUERIES)]
    return (cost(chain, hits), cost(chain, misses), cost(probe, hits), cost(probe, misses))


def theory(a):
    return (1 + a / 2, a, (1 + 1 / (1 - a)) / 2, (1 + 1 / (1 - a) ** 2) / 2)


def write_svg(rows, path):
    w, h, left, bottom, top, right = 720, 460, 60, 50, 40, 20
    xmax, ymax = 1.0, 55.0

    def sx(x):
        return left + (w - left - right) * x / xmax

    def sy(y):
        return h - bottom - (h - bottom - top) * min(y, ymax) / ymax

    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" font-family="sans-serif" font-size="12">' % (w, h),
           '<rect width="100%" height="100%" fill="white"/>',
           '<text x="%d" y="22" font-size="14" font-weight="bold">Chaining vs linear probing (M=%d): cost vs load factor</text>' % (left, M)]
    for g in range(0, 56, 10):
        out.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#ddd"/>' % (left, sy(g), w - right, sy(g)))
        out.append('<text x="%d" y="%.1f" text-anchor="end">%d</text>' % (left - 6, sy(g) + 4, g))
    for g in range(0, 11):
        out.append('<text x="%.1f" y="%d" text-anchor="middle">%.1f</text>' % (sx(g / 10), h - bottom + 18, g / 10))
    out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="black"/>' % (left, h - bottom, w - right, h - bottom))
    out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="black"/>' % (left, top, left, h - bottom))
    out.append('<text x="%d" y="%d" text-anchor="middle">load factor (n / M)</text>' % ((left + w - right) // 2, h - 10))
    out.append('<text transform="translate(16,%d) rotate(-90)" text-anchor="middle">average nodes / slots examined</text>' % ((top + h - bottom) // 2))
    # columns: 0 alpha, 1-4 measured (chain hit, chain miss, probe hit, probe miss), 5-8 theory
    series = [("chaining hit", 1, 5, "#1f77b4"), ("chaining miss", 2, 6, "#17becf"),
              ("probing hit", 3, 7, "#ff7f0e"), ("probing miss", 4, 8, "#d62728")]
    for name, mcol, tcol, color in series:
        tpts = " ".join("%.1f,%.1f" % (sx(r[0]), sy(r[tcol])) for r in rows)
        mpts = " ".join("%.1f,%.1f" % (sx(r[0]), sy(r[mcol])) for r in rows)
        out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="1.5" stroke-dasharray="6,4"/>' % (tpts, color))
        out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2"/>' % (mpts, color))
        for r in rows:
            out.append('<circle cx="%.1f" cy="%.1f" r="3" fill="%s"/>' % (sx(r[0]), sy(r[mcol]), color))
    ly = top + 10
    for i, (name, mcol, tcol, color) in enumerate(series):
        y = ly + 18 * i
        out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2"/>' % (left + 14, y, left + 44, y, color))
        out.append('<text x="%d" y="%d">%s (measured)</text>' % (left + 50, y + 4, name))
    y = ly + 18 * 4
    out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#555" stroke-dasharray="6,4"/>' % (left + 14, y, left + 44, y))
    out.append('<text x="%d" y="%d">dashed = theory</text>' % (left + 50, y + 4))
    out.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))


def main():
    rng = random.Random(SEED)
    rows = []
    head = ["load_factor", "chain_hit", "chain_miss", "probe_hit", "probe_miss",
            "chain_hit_theory", "chain_miss_theory", "probe_hit_theory", "probe_miss_theory"]
    print(("%6s" + " %10s" * 8) % tuple(head))
    for a in LOADS:
        runs = [run_once(a, rng) for _ in range(REPEATS)]
        meas = tuple(sum(r[i] for r in runs) / REPEATS for i in range(4))
        row = (a,) + tuple(round(x, 4) for x in meas) + tuple(round(x, 4) for x in theory(a))
        rows.append(row)
        print(("%6.2f" + " %10.3f" * 8) % row)
    with open(os.path.join(HERE, "compare_results.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(head)
        wr.writerows(rows)
    write_svg(rows, os.path.join(HERE, "compare_chart.svg"))


if __name__ == "__main__":
    main()
