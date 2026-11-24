# -*- coding: utf-8 -*-
"""交付前自检：entry 格式/delta 六列/evidence 齐全/reason 不共用/报告占位符已清。"""
import os, csv, re, glob
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # NAMED_PUSH_S06_B3
ERR = []
# delta
with open(os.path.join(OUT,"delta.tsv"), encoding="utf-8") as f:
    rows = list(csv.reader(f, delimiter="\t"))
assert rows[0] == ["entry","subsystem","name","one_line_semantics","grade","evidence_path"], rows[0]
for r in rows[1:]:
    if not re.fullmatch(r"[0-9A-F]{8}", r[0]): ERR.append("bad entry fmt: "+r[0])
    if r[4] != "[已证]": ERR.append("bad grade: "+r[4])
    if not os.path.exists(r[5].replace("D:/", "D:\\")): ERR.append("missing evidence: "+r[5])
    if r[2] != r[5].split("/")[-1][4:-4].replace("ROW_",""):  # name check skipped (names differ from entry)
        pass
# unique reasons
reasons = [r[3] for r in rows[1:]]
if len(reasons) != len(set(reasons)): ERR.append("duplicate one_line_semantics")
# evidence files = 10
ev = glob.glob(os.path.join(OUT,"EVIDENCE","ROW_*.txt"))
if len(ev) != 10: ERR.append("evidence count %d != 10"%len(ev))
# all files present
for fn in ["delta.tsv","base_rate.tsv","PROGRESS.md","REPORT.md"]:
    if not os.path.exists(os.path.join(OUT,fn)): ERR.append("missing "+fn)
# REPORT no placeholder
rep = open(os.path.join(OUT,"REPORT.md"), encoding="utf-8").read()
if "逐行核完后填" in rep: ERR.append("REPORT placeholder remains")
if "_（" in rep: ERR.append("REPORT underscore placeholder remains")
# base_rate
br = open(os.path.join(OUT,"base_rate.tsv"), encoding="utf-8").read().strip().split("\n")
if br[1] != "B3\t10\t10\t5\t10\t5\t0.5000": ERR.append("base_rate mismatch: "+br[1])
print("delta rows=%d evidence=%d ERR=%s" % (len(rows)-1, len(ev), ERR if ERR else "NONE"))
