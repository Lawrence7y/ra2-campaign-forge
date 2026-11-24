# -*- coding: utf-8 -*-
# _siv_probe_gate.py — 查看 lowered 内 GATE_CODE 段标记。只读。
import json
from pathlib import Path

def load_payload(p):
    t = Path(p).read_text(encoding="utf-8", errors="ignore")
    i = t.find("export const payload")
    j = t.find("{", i)
    depth = 0
    k = j
    in_str = False
    esc = False
    while k < len(t):
        c = t[k]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(t[j:k + 1])
        k += 1
    return None

P = r"D:\Project\ra2-campaign-forge\.zcode\workflow-runs\dwfrun-636adfc5-7ca1-4948-a711-f8027d8de9e2.mjs"
pl = load_payload(P)
low = pl["lowered"]
print("lowered len=" + str(len(low)))
idx = []
i = low.find("GATE_CODE")
while i >= 0:
    idx.append(i)
    i = low.find("GATE_CODE", i + 1)
print("GATE_CODE occurrences: " + str(idx))
for i in idx:
    print("--- @" + str(i) + " ---")
    print(repr(low[max(0, i - 80):i + 120]))
