# -*- coding: utf-8 -*-
# N4 gate reviewer: independent application of the PRE-EXISTING improved
# predicates (lead/gate_fp7_20261108/_g7_predicates.py) to the deliverable.
# Independent driver (own code); reads predicates from disk but does not modify.
import json, sys, importlib.util, hashlib, re
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")
PRED = ROOT / "lead/gate_fp7_20261108/_g7_predicates.py"
DOC = ROOT / "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md"
OUT = ROOT / "lead/n4_gate_verdict_20261109/_n4gv_predicates_out.json"

spec = importlib.util.spec_from_file_location("_n4gv_g7", PRED)
g7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g7)

t = DOC.read_text(encoding="utf-8")
REQ = ['逐行', '十四行', '九 hunk', '语义层 YES', '甲不再绑定', '不签 APPROVE_SCOPE', '未验']
BAN = ['可应用母本', '放行 N-5', '已应用', '已签 APPROVE_SCOPE']

p9, w9 = g7.r9_check(t, REQ)
p10, w10, h10 = g7.r10_scan(t, BAN)
p12, h12 = g7.r12_scan(t, BAN)
p11, w11, binds11 = g7.r11_scan(t, ROOT / "lead/n4_yi_final_20261108", root=ROOT)

# independent naive gate reconstruction (from GATE_CODE lines 12-21)
naive = []
for s in ['## 1','## 2','## 3','## 4','## 5','## 6']:
    if s not in t: naive.append('缺小节 '+s)
for k in REQ:
    if k not in t: naive.append('缺要素 '+k)
for bad in BAN:
    if bad in t: naive.append('含越权断言 '+bad)
if not re.findall(r'被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?', t):
    naive.append('缺 SHA256 绑定行')

res = {
    "pred_file": str(PRED.relative_to(ROOT)),
    "pred_sha256": hashlib.sha256(PRED.read_bytes()).hexdigest(),
    "doc_sha256": hashlib.sha256(DOC.read_bytes()).hexdigest(),
    "r9": {"problems": p9, "warnings": w9,
           "each": {k: g7.r9_element_present(t, k) for k in REQ}},
    "r10": {"problems": p10, "warnings": w10, "hits": h10},
    "r12": {"problems": p12, "hits": h12},
    "r11": {"problems": p11, "warnings": w11, "bindings": binds11},
    "naive_gate_problems": naive,
    "improved_gate_problems": p9 + p10 + p12 + p11,
}
OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=2))
