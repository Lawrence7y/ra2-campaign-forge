# -*- coding: utf-8 -*-
# 精确计数（多口径），供报告引用。只读，Python 不写文件。
import re, json

A = r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md"
B = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

def lines(p):
    with open(p, "rb") as f:
        return f.read().decode("utf-8", errors="replace").split("\n")

LA, LB = lines(A), lines(B)
ALL = [("PENDING", LA), ("GOAL", LB)]

pats = {
    "exit0_any": re.compile(r"exit\s*=\s*0|EXIT\s*=\s*0|CL_EXIT=0|LINK_EXIT=0|final_exit=0", re.I),
    "PASS_token": re.compile(r"\bPASS\b|SELF_TEST\s*=\s*PASS"),
    "verify_ok": re.compile(r"验证通过|机械检查通过|逐项通过"),
    "gate_run": re.compile(r"门禁.{0,20}实跑.{0,60}exit\s*=\s*0|门禁\s+exit\s*=\s*0"),
    "gate_word": re.compile(r"门禁"),
    "four_names": re.compile(r"check_d27|check_d29|check_d30|_rs_carrier_scan|carrier_scan|SELF_TEST|REFSYNC_SCOPE_FIX"),
    "broad": re.compile(r"exit\s*=\s*0|EXIT\s*=\s*0|\bPASS\b|通过|验证通过|机械检查通过|门禁|SELF_TEST|实跑|复跑|逐项通过|全绿|CL_EXIT|LINK_EXIT"),
}

def count(pat):
    out = {}
    for tag, ls in ALL:
        n = sum(1 for ln in ls if pat.search(ln))
        out[tag] = n
    out["TOTAL"] = out["PENDING"] + out["GOAL"]
    return out

res = {k: count(v) for k, v in pats.items()}

# 「门禁 实跑 exit=0」逐行清单（两台账）
gate_lines = []
for tag, ls in ALL:
    for i, ln in enumerate(ls, 1):
        if pats["gate_run"].search(ln):
            gate_lines.append({"file": tag, "line": i, "text": ln[:180]})
res["GATE_RUN_LINES"] = gate_lines
res["GATE_RUN_COUNT"] = len(gate_lines)

# 四件名字逐行清单
four_lines = []
for tag, ls in ALL:
    for i, ln in enumerate(ls, 1):
        if pats["four_names"].search(ln):
            four_lines.append({"file": tag, "line": i, "text": ln[:180]})
res["FOUR_NAME_LINES"] = four_lines
res["FOUR_NAME_COUNT"] = len(four_lines)

# 「验证通过」逐字
res["VERIFY_EXACT_LINES"] = [{"file": t, "line": i, "text": ln[:150]}
    for t, ls in ALL for i, ln in enumerate(ls, 1) if "验证通过" in ln]

print(json.dumps(res, ensure_ascii=False, indent=1))
