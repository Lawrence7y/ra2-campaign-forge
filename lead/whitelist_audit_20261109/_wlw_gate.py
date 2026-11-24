# -*- coding: utf-8 -*-
"""_wlw_gate.py — 撰写会话收尾自检：与编排方门禁同款（只读）。"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
ROOT = Path(r"D:\Project\ra2-campaign-forge")
wd = ROOT / "lead" / "whitelist_audit_20261109"
P = []
NB = 0
B = 0
STRICT = []
expected = wd / "WHITELIST_AUDIT.md"
if not expected.is_file():
    P.append("主交付件未按约定命名 WHITELIST_AUDIT.md")
else:
    t = expected.read_text(encoding="utf-8")
    NB = expected.stat().st_size
    for s in ["## 1", "## 2", "## 3", "## 4", "## 5", "## 6"]:
        if s not in t:
            P.append("缺小节 " + s)
    for k in ["白名单", "自证", "独立裁决", "语义在场", "部分满足", "反事实",
              "过宽", "过窄", "三分类", "可信度", "未验"]:
        if k not in t:
            P.append("缺要素 " + k)
    for bad in ["已移除白名单", "已改谓词", "已改交付件", "已修 R9"]:
        if bad in t:
            P.append("含越权断言 " + bad)
    B = len(re.findall(r"被核对象 SHA256 = [0-9a-fA-F]{64}", t))
    if B < 1:
        P.append("缺规范格式绑定行")
    STRICT = re.findall(r"被核对象 SHA256 = [0-9a-f]{64}，字节数 = \d+", t)
    if not STRICT:
        P.append("缺严格格式绑定行")

PRE = {
 "lead/gate_r9sem_20261109/_r9s_regress_out.json": "5bfb169acc58221ac74873dd99e1236931ac1b08d1eedc8dfb43076cc5b05e25",
 "lead/gate_r9sem_20261109/_r9s_predicates.py": "b0265fc57ef4facd06d92b4852344a80d983f14560a8521525ba18e533ae7034",
 "lead/gate_fp7_20261108/_g7_predicates.py": "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120",
 "lead/PENDING_DECISIONS.md": "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7",
 "lead/GOAL_THREE_TARGETS_20261018.md": "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede",
}
drift = []
for rel, pre in PRE.items():
    p = ROOT / rel
    cur = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "MISSING"
    if cur != pre:
        drift.append(rel)
        P.append("被改动 " + rel)
print(json.dumps({"ok": not P, "problems": P, "bindings": B,
                  "strict_bindings": len(STRICT), "docBytes": NB,
                  "readonly_5_drift": drift,
                  "doc_sha256": hashlib.sha256(expected.read_bytes()).hexdigest() if expected.is_file() else "MISSING"},
                 ensure_ascii=False))
