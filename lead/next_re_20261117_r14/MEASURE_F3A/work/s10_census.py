# -*- coding: utf-8 -*-
"""MEASURE-F3A step 5: per-row judgement + full census + the two outlier rows.

Emits F3A_CLASS.tsv (274 rows) and the per-subsystem "after downgrade" table.
"""
import csv, json, os, re, sys, collections, math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from pelib import PE
from thirdb import conds, thirdb, which

ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
BASE = os.path.join(ROOT, r"lead\next_re_20261117_r14\MEASURE_F3A")
EV = os.path.join(BASE, "EVIDENCE")
work = os.path.join(BASE, "work")
COLS = ["entry", "subsystem", "name", "one_line_semantics",
        "grade", "evidence_path", "n_sources", "conflict"]

pe = PE(EXE)
atlas_size, atlas_ninst = {}, {}
with open(ATLAS, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        atlas_size[r["entry"].upper()] = int(r["size"])
        atlas_ninst[r["entry"].upper()] = int(r["n_instr"])

rows = []
for i, line in enumerate(open(COV, encoding="utf-8-sig", newline="")):
    line = line.rstrip("\r\n")
    if not line or i == 0:
        continue
    rows.append(dict(zip(COLS, line.split("\t"))))

TAIL = re.compile(r"[（(]\s*名字已证\s*[，,]\s*语义(?:一行)?据名(?:推断)?\s*(?:\[未证\])?\s*[)）]\s*(?:\[未证\])?\s*$")
BODY = re.compile(r"^(?P<name>[^：]+)：YRpp/kb 地址名；归属 (?P<cat>.+)$")
ANCHOR = re.compile(r"\+0x[0-9A-Fa-f]+|\bcall\b|\bjmp\b|cmp\s|setne|sete|跳表|虚表槽|循环")

def wording_class(sem):
    core = TAIL.sub("", sem)
    if BODY.match(core):
        if re.search(r"[（(]名字已证，语义一行据名推断\[未证\][)）]\s*$", sem):
            return "TM-B_语义一行据名推断"
        return "TM-A_语义据名"
    return "OTH_非模板"

def judge(sem):
    """甲 = the row's own semantics already carries checkable ③b anchors.
       乙 = only name + class-belonging, no behaviour at all."""
    core = TAIL.sub("", sem)
    if ANCHOR.search(core):
        return "甲"
    return "乙"

dom = [r for r in rows if r["grade"] == "[已证]"
       and "[未证]" in r["one_line_semantics"] and r["subsystem"] != "S22"]
print("domain:", len(dom))

# ---- census
recs = []
for r in dom:
    e = r["entry"].upper()
    sem = r["one_line_semantics"]
    wc = wording_class(sem)
    v = judge(sem)
    c = conds(pe, int(e, 16), atlas_size[e])
    recs.append({"entry": e, "subsystem": r["subsystem"], "name": r["name"],
                 "wording": wc, "verdict": v,
                 "n_instr": c["n_instr"], "size": atlas_size[e],
                 "thirdb_bytes": thirdb(c), "thirdb_which": which(c),
                 "backedge": c["n_backedge"], "calls": c["n_call"],
                 "sem": sem, "ev": r["evidence_path"],
                 "objw": c["obj_writes"], "sentinel": c["sentinel"]})

cnt = collections.Counter((r["verdict"], r["wording"]) for r in recs)
print("\nverdict x wording:")
for k, v in sorted(cnt.items()):
    print("  %s / %-22s %3d" % (k[0], k[1], v))
print("\n甲 (text already carries checkable ③b): %d" % sum(1 for r in recs if r["verdict"] == "甲"))
print("乙 (only name+category, no behaviour)  : %d" % sum(1 for r in recs if r["verdict"] == "乙"))
print("\nof the 乙 rows, byte-side ③b demonstrable: %d  (rescue head-room, LOWER BOUND)"
      % sum(1 for r in recs if r["verdict"] == "乙" and r["thirdb_bytes"]))
print("of the 乙 rows, byte-side ③b NOT found    : %d"
      % sum(1 for r in recs if r["verdict"] == "乙" and not r["thirdb_bytes"]))

# ---- the two outliers, spelled out
print("\n===== the two non-template rows =====")
for r in recs:
    if r["wording"].startswith("OTH"):
        print("%s  %s  %s" % (r["entry"], r["subsystem"], r["name"]))
        print("   bytesthirdb=%s(%s) instr=%d" % (r["thirdb_bytes"], r["thirdb_which"], r["n_instr"]))
        print("   sem=%s" % r["sem"][:300])

# ---- per-subsystem table
def named_S(r):
    nm = (r["name"] or "").strip()
    return bool(nm) and not nm.startswith("sub_") and "::sub_" not in nm

subs = sorted({r["subsystem"] for r in rows if r["subsystem"] != "S22"})
table = {}
for s in subs:
    at = [r for r in rows if r["subsystem"] == s and r["entry"].upper() in atlas_size]
    n = len(at)
    proved = sum(1 for r in at if r["grade"] == "[已证]")
    f3 = [r for r in recs if r["subsystem"] == s]
    jia = sum(1 for r in f3 if r["verdict"] == "甲")
    yi = sum(1 for r in f3 if r["verdict"] == "乙")
    proved_after = proved - yi
    thr_n = math.ceil(0.9 * n)
    thr_p = math.ceil(0.5 * n)
    nm_s = sum(1 for r in at if named_S(r))
    ok = nm_s >= thr_n and proved_after >= thr_p
    table[s] = {"n": n, "named_S": nm_s, "thr_named": thr_n, "thr_proved": thr_p,
                "proved": proved, "f3a": len(f3), "jia": jia, "yi": yi,
                "proved_after": proved_after,
                "pct_before": round(100.0 * proved / n, 2) if n else 0,
                "pct_after": round(100.0 * proved_after / n, 2) if n else 0,
                "pass_before": nm_s >= thr_n and proved >= thr_p,
                "pass_after": ok}

print("\n%-4s %5s %6s %6s %5s %4s %4s %10s %10s %5s %s" %
      ("sub", "n", "prvB", "prvA", "thrP", "F3a", "甲", "proved", "proved'", "thrN", "达标后"))
for s in subs:
    d = table[s]
    print("%-4s %5d %6d %6d %5d %4d %4d %10s %10s %5d %s" % (
        s, d["n"], d["proved"], d["proved_after"], d["thr_proved"],
        d["f3a"], d["jia"], "%d/%d" % (d["proved"], d["n"]),
        "%d/%d" % (d["proved_after"], d["n"]), d["thr_named"],
        "OK" if d["pass_after"] else "-"))

pb = [s for s in subs if table[s]["pass_before"]]
pa = [s for s in subs if table[s]["pass_after"]]
print("\n达标 before: %d %s" % (len(pb), pb))
print("达标 after : %d %s" % (len(pa), pa))

json.dump({"table": table, "recs": recs}, open(os.path.join(work, "s10_census.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
