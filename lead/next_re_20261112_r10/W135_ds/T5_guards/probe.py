# -*- coding: utf-8 -*-
"""Probe helper: dump instruction context using the AUTHORITATIVE linear sweep
only (never re-decoding from an arbitrary offset)."""
import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "tg", os.path.join(os.path.dirname(os.path.abspath(__file__)), "t5_guards.py"))
# t5_guards runs main() only under __main__, so importing is safe.
tg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tg)

data, sha, ib, secs = tg.load()
img = tg.Image(data, ib, secs)
_n, tva, tvs, tro, trs = img.by_name[".text"]
tend = tva + min(trs, tvs)
sw = tg.Sweep(img, tva, tend)


def ctx(va, before=10, after=8):
    k = sw.idx(va)
    if k is None:
        print("0x%X NOT AN INSTRUCTION START" % va)
        return
    lo = max(0, k - before)
    hi = min(len(sw.order), k + after + 1)
    for j in range(lo, hi):
        a = sw.order[j]
        i = sw.at(a)
        mark = " <== SITE" if a == va else ""
        print("0x%06X  %-24s %-8s %s%s" % (a, i.bytes.hex(), i.mnemonic, i.op_str, mark))
    print("")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        va = int(arg, 16)
        print("=" * 70)
        print("0x%X" % va)
        print("=" * 70)
        ctx(va)
