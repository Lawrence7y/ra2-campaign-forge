#!/usr/bin/env python3
"""W131g: MERGED canonical subsystem map.

Why a merge is needed (cross-audit findings, ledger §854):
  * GLM's map (W130_atlas/glm_seg) reaches 78.8% but that headline includes
      - 2,615 P1 assignments that come from GENERIC CONTAINER classes only
        (VectorClass<T>/DynamicVectorClass<T>/...), which say nothing about the
        game subsystem, and
      - 1,059 region-fill + 1,519 cluster-fill assignments; the region-fill layer
        alone inflates AUDIO from ~25 real functions to 348 (only 8 of which have
        any audio evidence of their own).
  * My map (W131) is conservative (no generic classes, no region fill) but coarse
    (12 buckets) and caps at 42%.

Canonical rule: keep GLM's FINER taxonomy, but populate it only from
  T1 DIRECT evidence: GLM P1 with a non-generic class, GLM P0a/P2/P3-string,
     plus my L1..L4 projected onto GLM's label names.
  T2 INFERRED: call-graph propagation (>=70% of >=3 labelled neighbours), max 2 rounds.
Nothing else. Region/cluster fill is NOT used.
"""
import collections
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.join(os.path.dirname(HERE), "W130_atlas")
GLM = os.path.join(ATLAS, "glm_seg")

sys.path.insert(0, HERE)
from subsystem_map import class_subsys, module_subsys, import_subsys, string_subsys

# my coarse label -> GLM fine label
COARSE2FINE = {
    "COMBAT": "GameObj_Logic",
    "UI": "UI_Gadget_Dialog",
    "NET": "Net_Transport",
    "RENDER": "Graphics_Blit_Shape",
    "MAP": "Scenario_Map",
    "AI_SCRIPT": "AI_Team_Script",
    "RESOURCE_IO": "File_Mix_FS",
    "LOCOMOTION": "Movement_Locomotion",
    "SAVE_CAMPAIGN": "SaveLoad",
    "ENGINE_CORE": "Misc_Util_Mem",
    "AUDIO": "Audio_Sound_Music",
    "WORLD_DOMINATION": "WDT_WorldDom",
}

GENERIC = re.compile(
    r"(VectorClass|DynamicVectorClass|rc_ptr|TypeList|VectorCursor|CComObject|"
    r"TClassFactory|^\?\.\?AVNode|^\?\.\?AVList|Initializer|ReferenceCounted|"
    r"^\.\?AVBase|^\.\?AV?\.\$\$)")

DIRECT_GLM = {"P0a+module", "P2+import", "P3+string"}


def main():
    # ---------- inputs ----------
    size = {}
    with io.open(os.path.join(ATLAS, "function_atlas.tsv"), encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            p = line.rstrip("\n").split("\t")
            d = dict(zip(hdr, p))
            size[int(d["entry"], 16)] = (int(d["size"]), d)
    tot_bytes = sum(v[0] for v in size.values())

    fn_classes = collections.defaultdict(set)
    with io.open(os.path.join(HERE, "fn_class.tsv"), encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            fn_classes[int(p[0], 16)] = {c for c in p[1].split(",") if c}

    fn_mods = collections.defaultdict(set)
    with io.open(os.path.join(ATLAS, "module_attribution.tsv"), encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            fn_mods[int(p[0], 16)] = {m for m in p[3].split(",") if m}

    glm = {}
    with io.open(os.path.join(GLM, "function_assign.tsv"), encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            glm[int(p[0], 16)] = (p[1], p[2], p[3])

    callees = collections.defaultdict(set)
    callers = collections.defaultdict(set)
    with io.open(os.path.join(HERE, "calledges.raw.log"), encoding="utf-8",
                 errors="replace") as f:
        for ln in f:
            m = re.search(r"CallEdges\.java> ([0-9a-f]{8})\t([0-9a-f]{8})\t", ln)
            if not m:
                continue
            a, b = int(m.group(1), 16), int(m.group(2), 16)
            callees[a].add(b)
            callers[b].add(a)

    # ---------- T1: direct evidence ----------
    label = {}
    tier = {}
    for e, (sz, d) in size.items():
        # (a) GLM P1 but only when the class is non-generic
        g = glm.get(e)
        if g:
            sub, kind, _conf = g
            if kind == "P1+vtable":
                cs = fn_classes.get(e, set())
                real = [c for c in cs if not GENERIC.search(c)]
                if real and sub != "UNASSIGNED":
                    label[e] = sub
                    tier[e] = "T1:glm-vtable"
                    continue
            elif kind in DIRECT_GLM and sub != "UNASSIGNED":
                label[e] = sub
                tier[e] = "T1:" + kind
                continue
        # (b) my own layers projected onto GLM's taxonomy
        votes = collections.Counter()
        for c in fn_classes.get(e, ()):
            s = class_subsys(c)
            if s:
                votes[s] += 1
        if votes:
            label[e] = COARSE2FINE[votes.most_common(1)[0][0]]
            tier[e] = "T1:my-vtable"
            continue
        v2 = collections.Counter()
        for m in fn_mods.get(e, ()):
            s = module_subsys(m)
            if s:
                v2[s] += 1
        if v2:
            label[e] = COARSE2FINE[v2.most_common(1)[0][0]]
            tier[e] = "T1:my-module"
            continue
        s = import_subsys(d.get("first_import", ""))
        if s:
            label[e] = COARSE2FINE[s]
            tier[e] = "T1:my-import"
            continue
        s = string_subsys(d.get("strings", ""))
        if s:
            label[e] = COARSE2FINE[s]
            tier[e] = "T1:my-string"

    t1 = len(label)
    print("T1 (direct evidence): %d fn (%.1f%%)" % (t1, 100.0 * t1 / len(size)))

    # ---------- T2: call-graph propagation ----------
    for rnd in (1, 2):
        added = 0
        for e in size:
            if e in label:
                continue
            votes = collections.Counter()
            neigh = callees.get(e, set()) | callers.get(e, set())
            for n in neigh:
                if n in label:
                    votes[label[n]] += 1
            tot = sum(votes.values())
            if tot < 3:
                continue
            sub, c = votes.most_common(1)[0]
            if c / tot >= 0.70:
                label[e] = sub
                tier[e] = "T2:callgraph-r%d" % rnd
                added += 1
        print("T2 round %d: +%d" % (rnd, added))
        if added == 0:
            break

    # ---------- outputs ----------
    sub_f = collections.Counter()
    sub_b = collections.Counter()
    tier_f = collections.Counter()
    with io.open(os.path.join(HERE, "fn_subsystem_canonical.tsv"), "w",
                 encoding="utf-8") as f:
        f.write("entry\tsize\tsubsystem\ttier\tn_callers\n")
        for e in sorted(size):
            sz, d = size[e]
            s = label.get(e, "UNASSIGNED")
            t = tier.get(e, "-")
            tier_f[t] += 1
            if s != "UNASSIGNED":
                sub_f[s] += 1
                sub_b[s] += sz
            f.write("0x%08X\t%d\t%s\t%s\t%s\n"
                    % (e, sz, s, t, d.get("n_callers", "0")))

    assigned = sum(sub_f.values())
    ab = sum(sub_b.values())
    print("\nCANONICAL coverage: %d/%d fn (%.1f%%)  %d/%d bytes (%.1f%%)"
          % (assigned, len(size), 100.0 * assigned / len(size),
             ab, tot_bytes, 100.0 * ab / tot_bytes))
    print("\ntier distribution:")
    for k, v in tier_f.most_common():
        print("   %-22s %d" % (k, v))

    print("\n=== canonical subsystem table (GLM taxonomy, direct+callgraph only) ===")
    rows = []
    for sub in sorted(sub_f, key=lambda s: -sub_f[s]):
        rows.append({"subsystem": sub, "n_functions": sub_f[sub], "n_bytes": sub_b[sub]})
        print("   %-24s fn=%-5d bytes=%-9d" % (sub, sub_f[sub], sub_b[sub]))
    json.dump({"subsystems": rows, "tiers": dict(tier_f),
               "coverage": {"assigned": assigned, "total": len(size),
                            "assigned_bytes": ab, "total_bytes": tot_bytes}},
              open(os.path.join(HERE, "subsystem_map_canonical.json"), "w"), indent=1)
    with io.open(os.path.join(HERE, "subsystems_canonical.tsv"), "w", encoding="utf-8") as f:
        f.write("subsystem\tn_functions\tn_bytes\n")
        for r in rows:
            f.write("%s\t%d\t%d\n" % (r["subsystem"], r["n_functions"], r["n_bytes"]))
    print("\nwrote fn_subsystem_canonical.tsv / subsystems_canonical.tsv")


if __name__ == "__main__":
    main()
