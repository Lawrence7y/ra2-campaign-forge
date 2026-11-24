# -*- coding: utf-8 -*-
"""崩点3 补证⑤：验证 _dB_anchor_recompute.py:401-406 硬编码的 probe_expect 四组数
(n, waitMin, waitMed, waitMax) 与主探针 _dtrigger_probe_out.txt 既有实测行是否逐值一致，
即判定硬编码期望值的来源 = 既有探针落盘记录的转抄（冻结先验），非本轮从语料推导。
只读；路径全常量 + 包含校验。"""
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "lead"
WD = LEAD / "r2_unclosed_b_20261108"
OUT = WD / "_b_probe_expect_out.txt"
PROBE = LEAD / "dtrigger_compare_20261107" / "_dtrigger_probe_out.txt"

# 逐字转抄自 _dB_anchor_recompute.py:402-405（本轮直读）
PROBE_EXPECT_LITERAL = {
    "C2-abs-P95x2": (29, 66.334, 70.931, 321.002),
    "C3-r4":        (24, 125.884, 127.491, 440.389),
    "C3-r8":        (16, 251.709, 256.261, 258.378),
    "C3-r12":       (15, 377.385, 385.601, 387.990),
}

text = PROBE.read_text(encoding="utf-8-sig", errors="replace")
probe_lines = text.splitlines()

lines = []
lines.append("【主探针既有实测（正则实读 _dtrigger_probe_out.txt）】")
found = {}
cur = None
for i, ln in enumerate(probe_lines, 1):
    m = re.match(r"\s{2}(C2-abs-P95x2|C3-r4|C3-r8|C3-r12)\s+\[", ln)
    if m:
        cur = m.group(1)
        found.setdefault(cur, {"def_line": i})
        continue
    if cur:
        mt = re.search(r"nTrig=(\d+)", ln)
        if mt and "nTrig" not in found[cur]:
            found[cur]["nTrig"] = int(mt.group(1))
            found[cur]["nTrig_line"] = i
        mw = re.search(r"waitAfterS_hat\(ms\): min=([\d.]+) med=([\d.]+) .*max=([\d.]+)", ln)
        if mw and "min" not in found[cur]:
            found[cur]["min"] = float(mw.group(1))
            found[cur]["med"] = float(mw.group(2))
            found[cur]["max"] = float(mw.group(3))
            found[cur]["wait_line"] = i
        if re.match(r"\s{2}C\d", ln) and "[" not in ln:
            cur = None

all_ok = True
for cid, lit in PROBE_EXPECT_LITERAL.items():
    f_ = found.get(cid)
    if not f_:
        lines.append(f"{cid}: 探针件中未找到该档 —— NOT FOUND")
        all_ok = False
        continue
    probe_vals = (f_.get("nTrig"), f_.get("min"), f_.get("med"), f_.get("max"))
    ok = (probe_vals == lit)
    all_ok = all_ok and ok
    lines.append(f"{cid}:")
    lines.append(f"  硬编码字面 (_dB_anchor_recompute.py:402-405) = {lit}")
    lines.append(f"  探针实测 (:{f_.get('nTrig_line')}/:{f_.get('wait_line')}) = {probe_vals}")
    lines.append(f"  逐值相等 = {ok}")

lines.append("")
lines.append(f"四组硬编码值 == 主探针既有实测（逐值） = {all_ok}")
lines.append("含义：probe_expect 是主探针落盘记录的转抄（写脚本时冻结的先验），非本轮从语料推导。")

txt = "\n".join(lines) + "\n"
assert OUT.is_relative_to(WD)
OUT.write_text(txt, encoding="utf-8")
print(txt)
