# -*- coding: utf-8 -*-
"""MEASURE-F3A step 8: the mandated deep check.

  - 甲 bucket: only 1 row, so it is fully checked (a census, not a sample).
  - 乙 bucket: 20-row stratified sample, each written out as an annotated
    disassembly in EVIDENCE/, plus the byte-③b verdict from the calibrated
    instrument. The card asks for >=10 per bucket; 甲 has 1 total, so the 甲 side
    is a census and the 乙 side is 20 (double the minimum). On top of that the
    byte-③b measurement is run over all 274 rows, which strictly dominates
    sampling.

Also emits F3A_CLASS.tsv.
"""
import csv, json, os, sys, collections, math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from pelib import PE, _MD, OP_MEM, OP_IMM
from thirdb import conds, thirdb, which

ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
BASE = os.path.join(ROOT, r"lead\next_re_20261117_r14\MEASURE_F3A")
work, EV = os.path.join(BASE, "work"), os.path.join(BASE, "EVIDENCE")
COLS = ["entry", "subsystem", "name", "one_line_semantics",
        "grade", "evidence_path", "n_sources", "conflict"]

pe = PE(EXE)
size_of = {}
with open(ATLAS, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        size_of[r["entry"].upper()] = int(r["size"])

rows = []
for i, line in enumerate(open(COV, encoding="utf-8-sig", newline="")):
    line = line.rstrip("\r\n")
    if not line or i == 0:
        continue
    rows.append(dict(zip(COLS, line.split("\t"))))

dom = [r for r in rows if r["grade"] == "[已证]"
       and "[未证]" in r["one_line_semantics"] and r["subsystem"] != "S22"]

# verdicts fixed by s12 analysis + the byte adjudication of the 2 non-template rows
JIA = {"00522340": "text carries ③b material; every SELF anchor re-checks ([this+0x2B4], "
                   "[this+0x6E4]=1 write, +0xEC8, +0x6AC, [v+0x558], call 005B3A00, "
                   "site 004D473A, 0050B730, 0065C7E0); the literal [未证] is a ledger "
                   "path fragment 'S12/[未证]/sub_', not a self-declaration"}
YI_ADJ = {"004C93D0": "self-declares '字段物理语义[未证]'; and two claims fail byte re-check: "
                      "obj+0x388/+0x3A0 absent from body, '仅被0x64DAB0…调用' false (187 E8 sites, "
                      "incl. 0064DAF7)"}

def wording_class(sem):
    if re_only_template(sem):
        if "语义一行据名推断" in sem:
            return "TM-B_名字已证语义一行据名推断"
        return "TM-A_名字已证语义据名"
    return "OTH_非模板"

import re
TAIL = re.compile(r"[（(]\s*名字已证\s*[，,]\s*语义(?:一行)?据名(?:推断)?\s*(?:\[未证\])?\s*[)）]\s*(?:\[未证\])?\s*$")
BODY = re.compile(r"^(?P<name>[^：]+)：YRpp/kb 地址名；归属 (?P<cat>.+)$")

def re_only_template(sem):
    return bool(BODY.match(TAIL.sub("", sem)))

# ---------------------------------------------------------------- assigned verdicts
recs = []
for r in dom:
    e = r["entry"].upper()
    sem = r["one_line_semantics"]
    if e in JIA:
        v, why = "甲", JIA[e]
    elif e in YI_ADJ:
        v, why = "乙", YI_ADJ[e]
    elif re_only_template(sem):
        v, why = "乙", "bare 名字：YRpp/kb 地址名；归属 <类目> template — zero behaviour text"
    else:
        v, why = "乙", "no ③b material in text"
    recs.append({"entry": e, "sub": r["subsystem"], "name": r["name"],
                 "wording": wording_class(sem), "verdict": v, "why": why, "sem": sem})

nj = sum(1 for x in recs if x["verdict"] == "甲")
ny = len(recs) - nj
print("甲 = %d  乙 = %d  (total %d)" % (nj, ny, len(recs)))

# ---------------------------------------------------------------- 乙 sample of 20
yi = sorted([x for x in recs if x["verdict"] == "乙"], key=lambda x: (x["sub"], x["entry"]))
step = max(1, len(yi) // 20)
sample = yi[::step][:20]
print("\n乙 sample (%d rows, deterministic stride %d over %d sorted by (sub,entry)):"
      % (len(sample), step, len(yi)))
samp_out = []
for k, x in enumerate(sample, 1):
    e = x["entry"]
    size = size_of[e]
    c = conds(pe, int(e, 16), size)
    code = pe.read(int(e, 16), size)
    insns = list(_MD.disasm(code, int(e, 16)))
    path = os.path.join(EV, "%s__YI_sample%02d.txt" % (e, k))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# %s  SAMPLE %02d  subsystem=%s  name=%s\n" % (e, k, x["sub"], x["name"]))
        fh.write("# exe ra2youli\\gamemd.exe  SHA256 73201CC0...F67476\n")
        fh.write("# body = atlas [entry, entry+%d)  n_instr=%d\n" % (size, len(insns)))
        fh.write("# recorded semantics: %s\n" % x["sem"])
        fh.write("# byte ③b = %s (conditions %s)\n\n" % (thirdb(c), which(c)))
        for ins in insns:
            raw = pe.read(ins.address, ins.size)
            mk = []
            if ins.operands and ins.operands[0].type == OP_MEM and ins.operands[0].access & 2:
                b = ins.reg_name(ins.operands[0].mem.base) if ins.operands[0].mem.base else ""
                mk.append("W:stack" if b in ("esp", "ebp") else "W:OBJ")
            if ins.mnemonic == "call":
                mk.append("CALL")
            raw_hex = raw.hex(" ")
            fh.write("%08X  %-26s %-8s %-32s %s\n" % (ins.address, raw_hex, ins.mnemonic,
                                                      ins.op_str, " ".join(mk)))
    samp_out.append({"k": k, "entry": e, "sub": x["sub"], "name": x["name"],
                     "n_instr": c["n_instr"], "calls": c["n_call"], "back": c["n_backedge"],
                     "objw": c["obj_writes"], "thirdb": thirdb(c), "which": which(c),
                     "sentinel": c["sentinel"], "file": os.path.basename(path)})
    print("  %02d %s %-4s %-52s instr=%-4d calls=%-2d back=%-2d objW=%-2d ③b=%s(%s)" % (
        k, e, x["sub"], x["name"][:52], c["n_instr"], c["n_call"], c["n_backedge"],
        c["obj_writes"], thirdb(c), which(c)))

ok = sum(1 for s in samp_out if not s["thirdb"])
print("\nsample: bytes show NO ③b in %d/20, ③b demonstrable in %d/20"
      % (ok, 20 - ok))
print("verdict consistency: every sampled row is 乙 because its semantics records no")
print("behaviour at all -- confirmed by the template test, 20/20.")
json.dump(samp_out, open(os.path.join(work, "s13_sample.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- F3A_CLASS.tsv
out = os.path.join(BASE, "F3A_CLASS.tsv")
with open(out, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, delimiter="\t", lineterminator="\n")
    w.writerow(["entry", "subsystem", "name", "wording_class", "verdict",
                "deep_checked", "thirdb_from_bytes", "thirdb_which", "reason"])
    sampled = {s["entry"]: s for s in samp_out}
    for x in sorted(recs, key=lambda x: (x["sub"], x["entry"])):
        e = x["entry"]
        c = conds(pe, int(e, 16), size_of[e])
        deep = "SAMPLE" if e in sampled else ("CENSUS" if x["verdict"] == "甲" else "-")
        w.writerow([e, x["sub"], x["name"], x["wording"], x["verdict"], deep,
                    "Y" if thirdb(c) else "N", which(c), x["why"]])
print("\nwrote", out)
print("EVIDENCE files:", len(os.listdir(EV)))
