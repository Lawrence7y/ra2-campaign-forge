import json, collections, os, sys

Q3 = "_r209/q3.json"
OUTDIR = "_r210"
os.makedirs(OUTDIR, exist_ok=True)

q = json.load(open(Q3))
th = q["thunk"]           # hex str -> {va:int, kind:str, imm:int, jmp:int}
hit = q["hit"]            # COL hex str -> [[slot:int, thunkva:hex str], ...]
mdisp = q["mdisp"]        # COL hex str -> int
vt = q["vt"]              # COL hex str -> [hex str function va, ...]
names = q["names"]

# ---------- reverse index: thunk -> [(COL, slot), ...] ----------
rev = collections.defaultdict(list)
triples = collections.defaultdict(list)   # (s0,s1,s2) -> list of COL
for col, entries in hit.items():
    first3 = [e for e in entries if e[0] in (0, 1, 2)]
    for slot, tva in entries:
        rev[tva].append((col, slot))
    s = {e[0]: e[1] for e in first3}
    if set(s) == {0, 1, 2}:
        triples[(s[0], s[1], s[2])].append(col)

# ---------- assertions ----------
ck = {}

def check(name, cond, detail):
    ck[name] = "PASS" if cond else "FAIL"
    print("ASSERT %s %s: %s" % (name, ck[name], detail))

check("B1", len(th) == 70, "thunk count = %d (expect 70)" % len(th))
total_slots = 3 * len(hit)
in_set = sum(1 for col, entries in hit.items()
             for slot, tva in entries if slot in (0, 1, 2) and tva in th)
check("B2", in_set == total_slots,
      "first3 slots all thunk = %d/%d" % (in_set, total_slots))
check("B3", len(triples) == 23, "triple groups = %d (expect 23)" % len(triples))

jmp_groups = collections.defaultdict(list)
for tri in triples:
    j0, j1, j2 = (th[t]["jmp"] for t in tri)
    jmp_groups[(j0, j1, j2)].append(tri)
check("B4", len(jmp_groups) == 13, "jmp triple groups = %d (expect 13)" % len(jmp_groups))

orphans = sorted(set(th) - set(rev))
check("B5", len(orphans) == 0, "orphan thunks = %d %s" % (len(orphans), orphans))

uniq_md = all(len({mdisp[c] for c in cols}) == 1 for cols in triples.values())
check("B6", uniq_md, "each triple-group mdisp unique = %s" % uniq_md)

# ---------- evidence: group listing ----------
lines = []
def emit(s=""):
    print(s)
    lines.append(s)

emit("=== R210-B: 70 thunks / 23 triple groups / 13 jmp triples ===")
emit("q3 source: %s" % Q3)
emit("thunk=%d hit_tables=%d triple_groups=%d jmp_groups=%d" %
     (len(th), len(hit), len(triples), len(jmp_groups)))
emit("")
emit("--- B1..B6 assertions ---")
for k in ("B1", "B2", "B3", "B4", "B5", "B6"):
    emit("  %s=%s" % (k, ck[k]))
emit("")

emit("--- 1. Triple groups (23), sorted by first appearance ---")
tri_order = list(triples.keys())
for gi, tri in enumerate(tri_order, 1):
    cols = triples[tri]
    mds = sorted({mdisp[c] for c in cols})
    jmps = tuple(th[t]["jmp"] for t in tri)
    imms = tuple(th[t]["imm"] for t in tri)
    emit("G%02d: s0=%s s1=%s s2=%s  imm=(%d,%d,%d)  jmp=(%08x,%08x,%08x)  COLs=%d mdisp=%s  names=%s" %
         (gi, tri[0], tri[1], tri[2], imms[0], imms[1], imms[2],
          jmps[0], jmps[1], jmps[2], len(cols), mds,
          [names.get(c, "?") for c in cols[:3]]))
emit("")

emit("--- 2. jmp triples (13) and their triple-group/mdisp coverage ---")
for ji, (jt, tris) in enumerate(jmp_groups.items(), 1):
    tri_ids = [tri_order.index(t) + 1 for t in tris]
    mds = sorted({mdisp[c] for t in tris for c in triples[t]})
    emit("J%02d: jmp=(%08x,%08x,%08x)  groups=%s  mdisp=%s  triple_count=%d" %
         (ji, jt[0], jt[1], jt[2], tri_ids, mds, len(tris)))
emit("")

emit("--- 3. Pair-law: mdisp 4 and 24 in same jmp triple ---")
pair_families = []
for jt, tris in jmp_groups.items():
    allm = {mdisp[c] for t in tris for c in triples[t]}
    if 4 in allm and 24 in allm:
        pair_families.append((jt, tris, allm))
emit("same-jmp-family with both mdisp=4 and mdisp=24: %d families" % len(pair_families))
for jt, tris, allm in pair_families:
    ids = [tri_order.index(t) + 1 for t in tris]
    md4groups = [tri_order.index(t) + 1 for t in tris if mdisp[triples[t][0]] == 4]
    md24groups = [tri_order.index(t) + 1 for t in tris if mdisp[triples[t][0]] == 24]
    emit("  jmp=(%08x,%08x,%08x) groups=%s  mdisp=%s  md4_groups=%s md24_groups=%s" %
         (jt[0], jt[1], jt[2], ids, sorted(allm), md4groups, md24groups))
if not pair_families:
    emit("  (no family contains both mdisp=4 and mdisp=24 -> pair law NOT established)")
emit("")

emit("--- 4. All 70 thunks: address / kind / imm / E9 / refs / count ---")
for tva in sorted(th, key=lambda x: th[x]["va"]):
    v = th[tva]
    refs = rev.get(tva, [])
    refstr = ",".join("%s#%d" % (c, s) for c, s in refs[:6])
    if len(refs) > 6:
        refstr += "..."
    emit("%s kind=%s imm=%-5d jmp=%08x refs=%d [%s]" %
         (tva, v["kind"], v["imm"], v["jmp"], len(refs), refstr))
emit("orphan thunks (zero refs): %d %s" % (len(orphans), orphans))
emit("")

emit("--- 5. Core numbers ---")
emit("thunks=%d triple_groups=%d jmp_triples=%d paired_families=%d orphans=%d" %
     (len(th), len(triples), len(jmp_groups), len(pair_families), len(orphans)))

OUT_TXT = os.path.join(OUTDIR, "b1.txt")
with open(OUT_TXT, "w") as f:
    f.write("\n".join(lines) + "\n")

out = {
    "assertions": ck,
    "counts": {
        "thunks": len(th),
        "hit_tables": len(hit),
        "first3_slots_checked": total_slots,
        "triple_groups": len(triples),
        "jmp_triples": len(jmp_groups),
        "paired_families_4_24": len(pair_families),
        "orphan_thunks": len(orphans),
    },
    "triple_groups": [
        {
            "id": "G%02d" % gi,
            "slots": list(tri),
            "imm": [th[t]["imm"] for t in tri],
            "jmp": [th[t]["jmp"] for t in tri],
            "col_count": len(cols),
            "mdisp": sorted({mdisp[c] for c in cols}),
            "cols": cols,
        }
        for gi, tri in enumerate(tri_order, 1)
    ],
    "jmp_groups": [
        {
            "id": "J%02d" % ji,
            "jmp": list(jt),
            "group_ids": ["G%02d" % (tri_order.index(t) + 1) for t in tris],
            "mdisp": sorted({mdisp[c] for t in tris for c in triples[t]}),
        }
        for ji, (jt, tris) in enumerate(jmp_groups.items(), 1)
    ],
    "pair_law_4_24": [
        {
            "jmp": list(jt),
            "group_ids": ["G%02d" % (tri_order.index(t) + 1) for t in tris],
            "mdisp": sorted(allm),
            "md4_group_ids": ["G%02d" % (tri_order.index(t) + 1) for t in tris
                              if mdisp[triples[t][0]] == 4],
            "md24_group_ids": ["G%02d" % (tri_order.index(t) + 1) for t in tris
                               if mdisp[triples[t][0]] == 24],
        }
        for jt, tris, allm in pair_families
    ],
    "thunks": [
        {
            "va": tva,
            "kind": th[tva]["kind"],
            "imm": th[tva]["imm"],
            "jmp": th[tva]["jmp"],
            "ref_count": len(rev.get(tva, [])),
            "refs": rev.get(tva, []),
        }
        for tva in sorted(th, key=lambda x: th[x]["va"])
    ],
    "orphans": orphans,
}
OUT_JSON = os.path.join(OUTDIR, "b1.json")
with open(OUT_JSON, "w") as f:
    json.dump(out, f, indent=2)

if any(v != "PASS" for v in ck.values()):
    sys.exit(2)
