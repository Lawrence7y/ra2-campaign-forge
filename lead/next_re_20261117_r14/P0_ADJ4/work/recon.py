#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-ADJ4 recon: count UNDECIDABLE, extract first 100 by address, dump evidence field stats.
Read-only on gamemd.exe. Uses capstone 5.0.7 skipdata=True."""
import os, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
RES2WORK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_RESIDUAL_2\work"
if RES2WORK not in sys.path:
    sys.path.insert(0, RES2WORK)

ENUM = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_RESIDUAL_2\ENUM.tsv"

def rows_of(path):
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        h = f.readline().rstrip("\n").split("\t")
        for ln in f:
            if not ln.strip():
                continue
            p = ln.rstrip("\n").split("\t")
            if len(p) < len(h):
                p += [""] * (len(h) - len(p))
            out.append(dict(zip(h, p)))
    return out

def parse_ev(s):
    d = {}
    for tok in s.split(";"):
        if "=" in tok:
            k, v = tok.split("=", 1)
            d[k] = v
    return d

def main():
    rows = rows_of(ENUM)
    byverdict = collections.Counter(r["verdict"] for r in rows)
    print("TOTAL data rows =", len(rows))
    print("verdict distribution =", dict(byverdict))
    und = [r for r in rows if r["verdict"] == "UNDECIDABLE"]
    und.sort(key=lambda r: int(r["address"], 16))
    print("UNDECIDABLE =", len(und))
    sel = und[:100]
    print("selected first 100: %s .. %s" % (sel[0]["address"], sel[-1]["address"]))

    # evidence keys stats over selected 100
    fb = collections.Counter()
    pred = collections.Counter()
    tail = collections.Counter()
    flags = collections.Counter()
    reasons = collections.Counter()
    firstinsn_head = collections.Counter()
    for r in sel:
        ev = parse_ev(r["evidence"])
        fb[r["first_byte"]] += 1
        pred[r["predecessor"]] += 1
        tail[ev.get("tail", "?")] += 1
        reasons[r["undecidable_reason"]] += 1
        fi = r["first_insn"]
        firstinsn_head[fi.split()[0] + " " + (fi.split()[1] if len(fi.split()) > 1 else "")] += 1
        for k in ("inbody", "ptr", "call", "jmp", "fpu", "form(c4a|leaf)"):
            flags[(k, ev.get(k, "?"))] += 1
    print("\n-- first_byte hist (top 20):")
    for k, v in fb.most_common(20):
        print("  %-6s %d" % (k, v))
    print("\n-- predecessor hist:", dict(pred))
    print("-- tail hist:", dict(tail))
    print("-- reason hist:", dict(reasons))
    print("-- flags:")
    for k in sorted(flags):
        print("   ", k, flags[k])
    print("\n-- first_insn head (top 30):")
    for k, v in firstinsn_head.most_common(30):
        print("  %-28s %d" % (k, v))

    # write selected 100 to a working tsv
    outp = os.path.join(os.path.dirname(HERE), "SELECTED_100.tsv")
    with open(outp, "w", encoding="utf-8") as f:
        cols = ["address", "channel", "verdict", "align16", "first_byte", "predecessor",
                "prologue_or_leaf", "first_insn", "undecidable_reason", "evidence"]
        f.write("\t".join(cols) + "\n")
        for r in sel:
            f.write("\t".join(r[c] for c in cols) + "\n")
    print("\nwrote", outp)

if __name__ == "__main__":
    main()
