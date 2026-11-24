# -*- coding: utf-8 -*-
"""MEASURE-F3A step 4c: calibrate the two instruments SEPARATELY.

Instrument A — the (甲)/(乙) text criterion. Controls are about TEXT:
  positive (must judge 甲): a row whose semantics already writes checkable ③b anchors
  negative (must judge 乙): a row whose semantics is only class / slot / belonging

Instrument B — the ③b-from-bytes predicate. Controls come from documented bytes:
  positive: four rows whose text names ③b anchors; the anchors must resolve
  negative: 0045A640, documented as "pure compare loop, 0 writes 0 calls" ...

Mixing these two in one table is what produced the earlier mismatch, so they are
now scored independently.
"""
import csv, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from pelib import PE
from thirdb import conds, thirdb, which

ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
COLS = ["entry", "subsystem", "name", "one_line_semantics",
        "grade", "evidence_path", "n_sources", "conflict"]

pe = PE(EXE)
atlas = {}
with open(ATLAS, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        atlas[r["entry"].upper()] = int(r["size"])

cov = {}
for i, line in enumerate(open(COV, encoding="utf-8-sig", newline="")):
    line = line.rstrip("\r\n")
    if not line or i == 0:
        continue
    d = dict(zip(COLS, line.split("\t")))
    cov[d["entry"]] = d

# ---------------------------------------------------------------- instrument A
TAIL = re.compile(r"[（(]\s*名字已证\s*[，,]\s*语义(?:一行)?据名(?:推断)?\s*(?:\[未证\])?\s*[)）]\s*(?:\[未证\])?\s*$")
BODY = re.compile(r"^(?P<name>[^：]+)：YRpp/kb 地址名；归属 (?P<cat>.+)$")
ANCHOR = re.compile(r"\+0x[0-9A-Fa-f]+|\bcall\b|\bjmp\b|cmp\s|setne|sete|跳表|虚表槽|循环")

def judge_text(sem):
    """甲 if the text already carries checkable ③b anchors; 乙 if it is the bare
    'name + class-belonging' template with no behaviour at all."""
    core = TAIL.sub("", sem)
    if ANCHOR.search(core):
        return "甲", "text carries checkable anchors"
    if BODY.match(core):
        return "乙", "bare name+category template, zero behaviour text"
    return "乙", "no checkable anchor"

print("=== INSTRUMENT A : (甲)/(乙) text criterion ===")
A_CASES = [
    ("004A9840", "甲", "text: ③b② … 锚 +0x26 call 0x6DA230 / +0x2D cmp eax,-1 / +0x30 setne dl"),
    ("0065CDD0", "甲", "text: ③b②① … 锚 +0x52 call [7E11A0] / +0xAB cmp eax,-1"),
    ("004E2690", "甲", "text: ③b① … 锚 +0xC0 cmp [eax+4],ebx / +0xDC mov ax,[ebx+ecx*2]"),
    ("004AC660", "乙", "text: MapClass::SetSellMode：YRpp/kb 地址名；归属 …（名字已证，语义一行据名推断[未证]）"),
    ("004A80D0", "乙", "text: CD::GetCDNumber：YRpp/kb 地址名；归属 …"),
]
okA = 0
for e, want, note in A_CASES:
    got, why = judge_text(cov[e]["one_line_semantics"])
    okA += got == want
    print("%-9s want=%s got=%s  %-42s | %s" % (e, want, got, why, note[:60]))
print("A: %d/%d\n" % (okA, len(A_CASES)))

# ---------------------------------------------------------------- instrument B
print("=== INSTRUMENT B : ③b-from-bytes predicate ===")
B_CASES = [
    ("004A9840", True,  "text names ③b② → body must show the -1 sentinel"),
    ("006F3330", True,  "text names ③b② → body must show the -1 sentinel"),
    ("0065CDD0", True,  "text names ③b② → body must show cmp eax,-1"),
    ("00700600", True,  "text names ③b②+③b④ → bounded loop must show"),
    ("004A80D0", False, "2 instructions, ret 0xc only"),
    ("0045A640", False, "documented: pure compare loop, 0 writes, 0 calls → ③b must fail"),
    # consistency control: the only 甲 row of the domain must verify ③b, else the
    # 甲 verdict and the instrument contradict each other (card step 2).
    ("00522340", True,  "the 甲 row of the domain - its stated contract must verify"),
]
okB = 0
for e, want, note in B_CASES:
    c = conds(pe, int(e, 16), atlas[e])
    got = thirdb(c)
    okB += got == want
    print("%-9s want=%-5s got=%-5s ③b=%-4s instr=%-4d back=%-2d calls=%-2d  %s %s" % (
        e, want, got, which(c), c["n_instr"], c["n_backedge"], c["n_call"],
        note[:52], "" if got == want else "<== MISMATCH"))
print("B: %d/%d" % (okB, len(B_CASES)))

# informational (no documented truth asserted)
print("\n=== informational (instrument limits, no truth claimed) ===")
for e in ("004AC660", "004E2690"):
    c = conds(pe, int(e, 16), atlas[e])
    print("%-9s ③b=%-5s %-4s instr=%-4d back=%-2d  text-judge=%s" %
          (e, thirdb(c), which(c), c["n_instr"], c["n_backedge"],
           judge_text(cov[e]["one_line_semantics"])[0]))

if okA != len(A_CASES) or okB != len(B_CASES):
    print("\nCALIBRATION FAILED")
    sys.exit(1)
print("\nCALIBRATION PASSED (A %d/%d, B %d/%d)" % (okA, len(A_CASES), okB, len(B_CASES)))
json.dump({"A": okA, "A_n": len(A_CASES), "B": okB, "B_n": len(B_CASES)},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "s9_calib.json"),
               "w", encoding="utf-8"))
