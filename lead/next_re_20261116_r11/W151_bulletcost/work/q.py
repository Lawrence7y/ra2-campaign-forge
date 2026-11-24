# -*- coding: utf-8 -*-
"""W151 query helper over work/edges.tsv + work/absref.tsv + work/fnloops.tsv
Usage:
  python q.py callers 0x7192f0
  python q.py callees 0x7192f0
  python q.py refs 0xa8ed50
  python q.py fn 0x7192f0          # size/ninsn/nback/nloops
  python q.py loops <addr>...      # top-N functions by nback
  python q.py edge 0x55d360 0x67cef0
"""
import os, sys, csv, collections

ROOT = r"D:\Project\ra2-campaign-forge"
W = os.path.join(ROOT, r"lead\next_re_20261116_r11\W151_bulletcost\work")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas")


def load_edges():
    E = collections.defaultdict(list)   # caller -> [(callee,site)]
    R = collections.defaultdict(list)   # callee -> [(caller,site)]
    for line in open(os.path.join(W, "edges.tsv"), encoding="utf-8"):
        p = line.split()
        if len(p) != 3:
            continue
        a, b, s = p
        E[int(a, 16)].append((int(b, 16), int(s, 16)))
        R[int(b, 16)].append((int(a, 16), int(s, 16)))
    return E, R


def load_loops():
    d = {}
    for row in csv.DictReader(open(os.path.join(W, "fnloops.tsv"), encoding="utf-8"), delimiter="\t"):
        d[int(row["entry"], 16)] = (int(row["size"]), int(row["ninsn"]),
                                    int(row["nback"]), int(row["nloops"]))
    return d


def load_absref():
    d = collections.defaultdict(list)
    for line in open(os.path.join(W, "absref.tsv"), encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) < 5 or p[0] == "data_addr":
            continue
        d[int(p[0], 16)].append((int(p[2], 16), int(p[3], 16), p[4]))
    return d


E = R = L = A = None


def _ensure():
    global E, R, L, A
    if E is None:
        E, R = load_edges()
        L = load_loops()
        A = load_absref()


def nm(a):
    return "0x%08x" % a


def main():
    _ensure()
    cmd = sys.argv[1]
    if cmd == "callers":
        for x in sys.argv[2:]:
            v = int(x, 16)
            print("== callers of %s ==" % nm(v))
            for c, s in sorted(R.get(v, [])):
                print("   %s  site=%s" % (nm(c), nm(s)))
            print("   total=%d" % len(R.get(v, [])))
    elif cmd == "callees":
        for x in sys.argv[2:]:
            v = int(x, 16)
            print("== callees of %s ==" % nm(v))
            uniq = collections.Counter()
            for c, s in E.get(v, []):
                uniq[c] += 1
            for c, n in sorted(uniq.items()):
                print("   %s  x%d" % (nm(c), n))
            print("   unique=%d sites=%d" % (len(uniq), len(E.get(v, []))))
    elif cmd == "refs":
        for x in sys.argv[2:]:
            v = int(x, 16)
            print("== data xrefs to %s ==" % nm(v))
            for fn, site, txt in sorted(A.get(v, [])):
                print("   %s  %s : %s" % (nm(fn), nm(site), txt))
            print("   total=%d" % len(A.get(v, [])))
    elif cmd == "fn":
        for x in sys.argv[2:]:
            v = int(x, 16)
            z = L.get(v)
            if not z:
                print("%s  NOT IN ATLAS" % nm(v)); continue
            print("%s size=%d ninsn=%d nback=%d nloops=%d  callers=%d calleesites=%d" % (
                nm(v), z[0], z[1], z[2], z[3], len(R.get(v, [])), len(E.get(v, []))))
    elif cmd == "loops":
        print("== top 40 functions by back-edge count ==")
        for e, z in sorted(L.items(), key=lambda kv: -kv[1][2])[:40]:
            print("  %s size=%-6d ninsn=%-6d nback=%-4d nloops=%-3d" % (nm(e), z[0], z[1], z[2], z[3]))
    elif cmd == "edge":
        a, b = int(sys.argv[2], 16), int(sys.argv[3], 16)
        print("sites %s -> %s : %s" % (nm(a), nm(b), [nm(s) for c, s in E.get(a, []) if c == b]))


main()
