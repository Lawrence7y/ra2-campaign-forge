#!/usr/bin/env python3
# 导出 266 件平票明细，供设计冲突类型分型
import csv, os, re
LEAD = r"D:\Project\ra2-campaign-forge\lead"
R = os.path.join(LEAD, "next_re_20261117_r14")
VD = os.path.join(R, "R17_R81_T2_EVID", "_verdicts.tsv")
CM = os.path.join(R, "R17_R81_T2_EVID", "_content_metrics.tsv")
UD = os.path.join(R, "R17_R81_T2_EVID", "_undead_evid.tsv")
OUT = os.path.join(R, "R17_R84_T2_EVID2", "tie_dump.txt")
def load(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))
vd = load(VD); cm = {r["rel"]: r for r in load(CM)}; ud = {r["rel"]: r for r in load(UD)}
tie = [r for r in vd if r["verdict"] == "无法判定"]
PROC_KW = re.compile(r"stdout|stderr|_out\.|report|result|log|console|exit|run_id|cmd|trace|progress|selftest|check|probe|status|summary|verdict", re.I)
OBJ_KW = re.compile(r"row_|addr|disasm|bytes|byte|va|vaddr|site|table|vtable|struct|insn|instruction|cache|import|export|pe_|\bpe\b|dump|scan|map|ref|fact|index", re.I)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(f"TIE count={len(tie)}\n")
    for i, r in enumerate(sorted(tie, key=lambda x: x["rel"]), 1):
        rel = r["rel"]
        bn = os.path.basename(rel)
        x = cm[rel]; u = ud[rel]
        f.write(f"[{i:03d}] {rel}\n")
        f.write(f"     bn={bn} bnform={u['bnform']} ext={u['ext']} bytes={u['bytes']} O={r['O']} P={r['P']} varatio={x['varatio']} nlines={x['nlines']}\n")
        f.write(f"     nameProc={bool(PROC_KW.search(bn))} nameObj={bool(OBJ_KW.search(bn))}\n")
        f.write(f"     HEAD: {x['head'][:160]}\n")
print("wrote", OUT, "lines", len(tie))
