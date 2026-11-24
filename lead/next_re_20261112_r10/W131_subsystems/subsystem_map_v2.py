#!/usr/bin/env python3
"""W131e: subsystem map v2 with L5 = CALL-GRAPH PROPAGATION.

Design (evidence-ordered, every assignment carries its layer):
  L1 vtable class -> subsystem        (strongest: the function IS a method)
  L2 Westwood source file name        (strong: __FILE__ in an assert)
  L3 imported API signature           (medium)
  L4 referenced string keywords       (medium)
  L5 call-graph propagation           (inferential: majority of labelled
                                       neighbours agree; needs >=3 labelled
                                       neighbours and >=70% agreement)
  L6 imported-API co-occurrence       (weak; skipped -- would be guessing)

L5 is deliberately conservative and iterated at most 2 times, because each round
of propagation compounds error. Everything assigned by L5 is tagged so a reader
can exclude it.
"""
import collections
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS_DIR = os.path.join(os.path.dirname(HERE), "W130_atlas")
sys.path.insert(0, HERE)

from subsystem_map import (SUBSYS, class_subsys, module_subsys, import_subsys,
                           string_subsys)


def main():
    # ---- atlas ----
    fns = {}
    with io.open(os.path.join(ATLAS_DIR, "function_atlas.tsv"), encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            p = line.rstrip("\n").split("\t")
            d = dict(zip(hdr, p))
            fns[int(d["entry"], 16)] = d
    print("functions: %d" % len(fns))

    # ---- L1 tables ----
    fn_classes = collections.defaultdict(set)
    with io.open(os.path.join(HERE, "fn_class.tsv"), encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            for c in p[1].split(","):
                if c:
                    fn_classes[int(p[0], 16)].add(c)

    fn_mods = collections.defaultdict(set)
    with io.open(os.path.join(ATLAS_DIR, "module_attribution.tsv"), encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            for m in p[3].split(","):
                if m:
                    fn_mods[int(p[0], 16)].add(m)

    # ---- call graph ----
    callees = collections.defaultdict(set)
    callers = collections.defaultdict(set)
    with io.open(os.path.join(HERE, "calledges.raw.log"), encoding="utf-8",
                 errors="replace") as f:
        for ln in f:
            m = re.search(r"CallEdges\.java> ([0-9a-f]{8})\t([0-9a-f]{8})\t([0-9a-f]{8})", ln)
            if not m:
                continue
            a, b = int(m.group(1), 16), int(m.group(2), 16)
            callees[a].add(b)
            callers[b].add(a)
    print("edges: %d  callers-with-edges: %d" % (sum(len(v) for v in callees.values()),
                                                 len(callers)))

    # ---- L1..L4 ----
    label = {}
    for entry, d in fns.items():
        sub = why = None
        votes = collections.Counter()
        for c in fn_classes.get(entry, ()):
            s = class_subsys(c)
            if s:
                votes[s] += 1
        if votes:
            sub, why = votes.most_common(1)[0][0], "L1:vtable-class"
        if sub is None:
            v2 = collections.Counter()
            for m in fn_mods.get(entry, ()):
                s = module_subsys(m)
                if s:
                    v2[s] += 1
            if v2:
                sub, why = v2.most_common(1)[0][0], "L2:source-module"
        if sub is None:
            s = import_subsys(d.get("first_import", ""))
            if s:
                sub, why = s, "L3:import"
        if sub is None:
            s = string_subsys(d.get("strings", ""))
            if s:
                sub, why = s, "L4:string"
        if sub:
            label[entry] = (sub, why)

    base_assign = len(label)
    print("\nL1-L4 assigned: %d (%.1f%%)" % (base_assign, 100.0 * base_assign / len(fns)))

    # ---- L5 propagation, max 2 rounds, conservative ----
    for rnd in (1, 2):
        added = 0
        for entry in fns:
            if entry in label:
                continue
            votes = collections.Counter()
            neigh = set(callees.get(entry, ())) | set(callers.get(entry, ()))
            for n in neigh:
                if n in label:
                    votes[label[n][0]] += 1
            total = sum(votes.values())
            if total < 3:
                continue
            sub, cnt = votes.most_common(1)[0]
            if cnt / total >= 0.70:
                label[entry] = (sub, "L5:callgraph-r%d" % rnd)
                added += 1
        print("L5 round %d added: %d" % (rnd, added))
        if added == 0:
            break

    # ---- outputs ----
    sub_fns = collections.Counter()
    sub_bytes = collections.Counter()
    sub_range = {}
    layer = collections.Counter()
    with io.open(os.path.join(HERE, "fn_subsystem_v2.tsv"), "w", encoding="utf-8") as f:
        f.write("entry\tsize\tsubsystem\tevidence\tn_callers\n")
        for entry in sorted(fns):
            d = fns[entry]
            sub, why = label.get(entry, ("UNASSIGNED", "-"))
            size = int(d["size"])
            layer[why if why != "-" else "UNASSIGNED"] += 1
            if sub != "UNASSIGNED":
                sub_fns[sub] += 1
                sub_bytes[sub] += size
                lo, hi = sub_range.get(sub, (entry, entry))
                sub_range[sub] = (min(lo, entry), max(hi, entry))
            f.write("0x%08X\t%d\t%s\t%s\t%s\n"
                    % (entry, size, sub, why, d.get("n_callers", "0")))

    tot_bytes = sum(int(d["size"]) for d in fns.values())
    assigned = sum(sub_fns.values())
    print("\n=== evidence layers ===")
    for k, v in layer.most_common():
        print("  %-22s %d" % (k, v))
    print("\nassigned %d/%d (%.1f%%); bytes %d/%d (%.1f%%)"
          % (assigned, len(fns), 100.0 * assigned / len(fns),
             sum(sub_bytes.values()), tot_bytes,
             100.0 * sum(sub_bytes.values()) / tot_bytes))

    print("\n=== subsystem table v2 ===")
    rows = []
    for sub in SUBSYS:
        if sub_fns[sub] == 0:
            continue
        lo, hi = sub_range[sub]
        rows.append({"subsystem": sub, "n_functions": sub_fns[sub],
                     "n_bytes": sub_bytes[sub], "addr_lo": "0x%08X" % lo,
                     "addr_hi": "0x%08X" % hi})
        print("  %-17s fn=%-5d bytes=%-9d 0x%08X..0x%08X"
              % (sub, sub_fns[sub], sub_bytes[sub], lo, hi))
    with io.open(os.path.join(HERE, "subsystems_v2.tsv"), "w", encoding="utf-8") as f:
        f.write("subsystem\tn_functions\tn_bytes\taddr_lo\taddr_hi\n")
        for r in rows:
            f.write("%s\t%d\t%d\t%s\t%s\n" % (r["subsystem"], r["n_functions"],
                                              r["n_bytes"], r["addr_lo"], r["addr_hi"]))
    json.dump({"subsystems": rows, "evidence": dict(layer),
               "coverage": {"assigned": assigned, "total": len(fns),
                            "assigned_bytes": sum(sub_bytes.values()),
                            "total_bytes": tot_bytes}},
              open(os.path.join(HERE, "subsystem_map_v2.json"), "w"), indent=1)
    print("\nwrote fn_subsystem_v2.tsv / subsystems_v2.tsv / subsystem_map_v2.json")


if __name__ == "__main__":
    main()
