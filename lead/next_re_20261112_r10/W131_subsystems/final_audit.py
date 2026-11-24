#!/usr/bin/env python3
"""W131j: final CONSISTENCY AUDIT of every delivered artifact.

Goal-completion evidence: the five milestone artifacts must be mutually consistent
(counts must agree across files) and re-derivable.
"""
import collections
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.dirname(HERE)
ATLAS = os.path.join(A, "W130_atlas")
ok = True


def check(label, cond, detail=""):
    global ok
    ok &= bool(cond)
    print("  %-58s %s %s" % (label, "OK" if cond else "FAIL", detail))


def tsv_rows(path, has_header=True):
    n = 0
    with io.open(path, encoding="utf-8") as f:
        for i, _ in enumerate(f):
            n += 1
    return n - (1 if has_header else 0)


print("=== 1. class atlas (milestone 1) ===")
cls = json.load(open(os.path.join(ATLAS, "class_atlas_v2.json"), encoding="utf-8"))
vtc = json.load(open(os.path.join(ATLAS, "vtables_canonical.json"), encoding="utf-8"))
check("class_atlas_v2 classes == 988", cls["stats"]["classes_total"] == 988,
      "got %d" % cls["stats"]["classes_total"])
check("  of which with vtable == 954", cls["stats"]["with_vtable"] == 954,
      "got %d" % cls["stats"]["with_vtable"])
check("  interface-only == 34", cls["stats"]["interface_only"] == 34,
      "got %d" % cls["stats"]["interface_only"])
check("vtables_canonical count == 1214", vtc["stats"]["count"] == 1214,
      "got %d" % vtc["stats"]["count"])
check("  primary (COL.offset==0) == 954", vtc["stats"]["primary"] == 954,
      "got %d" % vtc["stats"]["primary"])
check("  classes in vtables == 954", vtc["stats"]["classes"] == 954,
      "got %d" % vtc["stats"]["classes"])

print("\n=== 2. function atlas (milestone 2) ===")
fa = os.path.join(ATLAS, "function_atlas.tsv")
n_fa = tsv_rows(fa)
check("function_atlas rows == 12916", n_fa == 12916, "got %d" % n_fa)
tot_b = 0
fnptr = 0
with io.open(fa, encoding="utf-8") as f:
    h = f.readline().rstrip("\n").split("\t")
    for line in f:
        p = line.rstrip("\n").split("\t")
        d = dict(zip(h, p))
        tot_b += int(d["size"])
        fnptr += 1 if d["is_fnptr"] == "1" else 0
check("total code bytes == 3225845", tot_b == 3225845, "got %d" % tot_b)
check("fn-pointer entries == 6303", fnptr == 6303, "got %d" % fnptr)
check(".text coverage >= 79%", tot_b / 4060045 >= 0.79,
      "%.1f%%" % (100.0 * tot_b / 4060045))

print("\n=== 3. subsystem map (milestone 3) ===")
sc = os.path.join(HERE, "fn_subsystem_canonical.tsv")
n_sc = tsv_rows(sc)
check("fn_subsystem_canonical rows == 12916", n_sc == 12916, "got %d" % n_sc)
smap = json.load(open(os.path.join(HERE, "subsystem_map_canonical.json"), encoding="utf-8"))
check("coverage.assigned == 5493", smap["coverage"]["assigned"] == 5493,
      "got %d" % smap["coverage"]["assigned"])
check("coverage.assigned_bytes == 2089876",
      smap["coverage"]["assigned_bytes"] == 2089876,
      "got %d" % smap["coverage"]["assigned_bytes"])
check("subsystem count == 26", len(smap["subsystems"]) == 26,
      "got %d" % len(smap["subsystems"]))
n_ent = tsv_rows(os.path.join(HERE, "subsystem_entries.tsv"))
check("subsystem_entries rows >= 20", n_ent >= 20, "got %d" % n_ent)
# every function in the atlas must appear exactly once in the subsystem file
ents_atlas = set()
with io.open(fa, encoding="utf-8") as f:
    f.readline()
    for line in f:
        ents_atlas.add(int(line.split("\t")[0], 16))
ents_sub = []
with io.open(sc, encoding="utf-8") as f:
    f.readline()
    for line in f:
        ents_sub.append(int(line.split("\t")[0], 16))
check("subsystem file covers the atlas exactly (no dup, no gap)",
      len(ents_sub) == len(set(ents_sub)) == len(ents_atlas) == 12916
      and set(ents_sub) == ents_atlas)

print("\n=== 4. structure entries (milestone 4) ===")
fc = os.path.join(HERE, "field_layout_classes.tsv")
fs = os.path.join(HERE, "field_layout_subsystems.tsv")
n_fc, n_fs = tsv_rows(fc), tsv_rows(fs)
check("field_layout_classes rows >= 300", n_fc >= 300, "got %d" % n_fc)
check("field_layout_subsystems rows > 2000", n_fs > 2000, "got %d" % n_fs)
check("FIELD_LAYOUT.md exists > 8KB",
      os.path.getsize(os.path.join(HERE, "FIELD_LAYOUT.md")) > 8000)
check("vtable_members rows == 13351", tsv_rows(os.path.join(HERE, "vtable_members.tsv")) == 13351,
      "got %d" % tsv_rows(os.path.join(HERE, "vtable_members.tsv")))
check("fn_class rows == 6256", tsv_rows(os.path.join(HERE, "fn_class.tsv")) == 6256,
      "got %d" % tsv_rows(os.path.join(HERE, "fn_class.tsv")))

print("\n=== 5. gradings present ===")
ledger = os.path.join(os.path.dirname(A), "GOAL_THREE_TARGETS_20261018.md")
txt = io.open(ledger, encoding="utf-8").read()
for sec in ("§846", "§847", "§848", "§849", "§850", "§851", "§852",
            "§853", "§854", "§855", "§856", "§857", "§858"):
    check("ledger has %s" % sec, sec in txt)
check("ledger has [已证] markers", txt.count("[已证") > 500, "count=%d" % txt.count("[已证"))
check("ledger has [未证] markers", txt.count("[未证") > 50, "count=%d" % txt.count("[未证"))

print("\n=== 6. scripts re-derivable ===")
for s in ("vtables_rebuild.py", "atlas_v2.py", "class_atlas_v2.py", "reconcile_vtables.py"):
    check("W130_atlas/%s" % s, os.path.exists(os.path.join(ATLAS, s)))
for s in ("vtable_members.py", "subsystem_map_v2.py", "merge_canonical.py",
          "subsystem_structure.py", "emit_fieldlist.py", "aggregate_fields.py",
          "CreateVtableFuncs.java", "CallEdges.java", "FieldLayout.java"):
    check("W131_subsystems/%s" % s, os.path.exists(os.path.join(HERE, s)))

print("\nOVERALL:", "PASS" if ok else "FAIL")
