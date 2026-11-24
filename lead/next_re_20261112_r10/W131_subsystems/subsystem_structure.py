#!/usr/bin/env python3
"""W131f: MILESTONE (4) -- subsystem entry points, hubs and drivers.

For each subsystem produced by W131e, compute from the 62k-edge call graph:
  * ENTRY   : functions with no in-edges from the same subsystem (called from
              outside, or not called at all) -- i.e. the subsystem's public face
  * HUB     : functions with the most in-subsystem callees (the workhorses)
  * DRIVER  : functions outside the subsystem that call into it the most
              (who owns this subsystem)
Also identifies plausible top-level drivers overall (gamesequence/main loop
candidates) by out-degree across subsystems.
"""
import collections
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.join(os.path.dirname(HERE), "W130_atlas", "function_atlas.tsv")


def main():
    # labels
    label = {}
    size = {}
    with io.open(os.path.join(HERE, "fn_subsystem_v2.tsv"), encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            e = int(p[0], 16)
            label[e] = p[2]
            size[e] = int(p[1])

    # callers/callees
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

    subs = sorted({s for s in label.values() if s != "UNASSIGNED"})
    report = {}
    print("=== subsystem structure (entry / hub / drivers) ===")
    for sub in subs:
        members = {e for e, s in label.items() if s == sub}
        # entry: no in-edge from same subsystem
        entry = []
        for e in members:
            ins = callers.get(e, set()) & members
            if not ins:
                entry.append(e)
        # hub: most in-subsystem callees
        hub = sorted(members, key=lambda e: -len(callees.get(e, set()) & members))[:5]
        # drivers: outside functions calling into this subsystem
        drv = collections.Counter()
        for e in members:
            for c in callers.get(e, ()):
                if label.get(c, "UNASSIGNED") != sub:
                    drv[c] += 1
        report[sub] = {
            "n_functions": len(members),
            "n_entry": len(entry),
            "entry_top": ["0x%08X" % e for e in sorted(entry)[:6]],
            "hub_top": [("0x%08X" % e, len(callees.get(e, set()) & members)) for e in hub],
            "drivers_top": [("0x%08X" % c, n, label.get(c, "UNASSIGNED"))
                            for c, n in drv.most_common(6)],
        }
        print("\n--- %s  (%d functions, %d entries)" % (sub, len(members), len(entry)))
        print("   entry samples : %s" % ", ".join(report[sub]["entry_top"][:4]))
        print("   hubs          : %s"
              % ", ".join("%s(%d)" % (a, n) for a, n in report[sub]["hub_top"][:3]))
        print("   driven by     : %s"
              % ", ".join("%s[%s]x%d" % (a, s, n) for a, n, s in report[sub]["drivers_top"][:4]))

    # ---- global top drivers: functions whose callees span many subsystems ----
    print("\n=== top cross-subsystem drivers (candidate main-loop / init) ===")
    span = []
    for e in set(list(callees.keys())):
        cs = callees.get(e, set())
        if len(cs) < 8:
            continue
        subs_hit = collections.Counter(label.get(c, "UNASSIGNED") for c in cs)
        nsub = len([s for s in subs_hit if s != "UNASSIGNED"])
        span.append((nsub, len(cs), e, subs_hit))
    span.sort(reverse=True)
    for nsub, ncallee, e, hits in span[:15]:
        top = ", ".join("%s:%d" % (k, v) for k, v in hits.most_common(4))
        print("   0x%08X  callees=%-4d subsystems=%-2d  %s  [self=%s]"
              % (e, ncallee, nsub, top, label.get(e, "UNASSIGNED")))

    json.dump({"per_subsystem": report,
               "cross_drivers": [{"fn": "0x%08X" % e, "callees": n, "subsystems": s}
                                 for s, n, e, _ in span[:30]]},
              open(os.path.join(HERE, "subsystem_structure.json"), "w"), indent=1)
    print("\nwrote subsystem_structure.json")


if __name__ == "__main__":
    main()
