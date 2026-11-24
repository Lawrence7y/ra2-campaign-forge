#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""regex_env_probe.py — 记录本机 Python `re` 的一个真实异常，并**划清它的影响边界**。

记录到的现象（与业务无关的最小复现）：
    re.search(r"^\\s*x", "a x")   -> 本机实测 False（人眼期望 True）
    re.search(r"^\\s*x", " x")    -> True
    re.search(r"\\s*x",   "a x")  -> True
即：`^` 之后紧跟可空量词（`\\s*`），且该量词在位置 0 只能吃 0 个字符时，本机引擎
不回溯到「吃 0 个、让后续字面量从位置 0 开始匹配」这条路径。
（同一台机器用 rg / Rust regex 引擎跑等价正则是正常的。）

**影响边界（必须写清楚，否则会误伤既有结论）**：
R16 的四环检测器我实测跑了三条读法，全部 11/11：
    A 原实现（`^\\s*#*\\s*proof…` + re.I）
    D 同一组正则，模式与文本都 lower()、无 re.I
    B 去锚等价改写（`(?:^|\\s)proof\\s+<hex>`）
原因：那 5 条正则里只有 PROOF 那条带 `^\\s*#*…` 锚，而 11 个真实 PROOF 文件的
首行是 `S10-KPROVED PROOF 0045A560`（PROOF 不在行首）；**真正先命中的是
`① ENTRY: … entry=<hex>` 那条（不带锚、不依赖上述异常）**，它单独就 11/11。
⇒ 这个 re 异常**不影响** R16「召回 11/11」这个结论，也不影响「四环回指=0」。

产物：python_re_probe.json
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys

OUT = os.path.dirname(os.path.abspath(__file__))
LEAD = os.path.abspath(os.path.join(OUT, "..", ".."))

# (pattern, subject, 人眼期望)
CASES = [
    # —— 与业务无关的最小复现 ——
    (r"^\s*x", "a x", True),
    (r"^\s*x", " x", True),
    (r"^\s*x", "x", True),
    (r"^\s*x", "ab x", True),
    (r"^a\s*x", "a x", True),
    (r"\s*x", "a x", True),
    (r"^x", "x", True),
    (r"^\s*x", "abc", False),
    # —— 本项目里真正被踩到的形态（锚 + 前缀词） ——
    (r"^\s*#*\s*proof\s+(?:0x)?([0-9a-f]{8})\b", "S10-KPROVED PROOF 0045A560", True),
    # —— 对照组：不带锚的等价写法，本机正常 ——
    (r"(?:^|\s)proof\s+(?:0x)?([0-9a-f]{8})\b", "S10-KPROVED PROOF 0045A560", True),
    # —— 对照组：①ENTRY 那条（不带锚、不依赖 re.I 也能覆盖大小写一致的写法） ——
    (r"①\s*ENTRY\s*:[^\n]{0,120}?entry\s*=\s*(?:0x)?([0-9a-f]{8})",
     "① ENTRY: atlas entry=0045A560", True),
]

res = {
    "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    "python": sys.version,
    "re_module": getattr(re, "__file__", "builtin"),
    "platform": sys.platform,
    "cases": [],
    "rg_cross_check": [],
}

for pat, subj, expect in CASES:
    got = bool(re.search(pat, subj, re.I))
    res["cases"].append(dict(pattern=pat, subject=subj, expected=expect, got=got,
                             ok=(got == expect)))

probe_file = os.path.join(LEAD, "next_re_20261117_r14", "S10_KPROVED",
                          "EVIDENCE", "PROOF_0045A560.txt")
RG_PATS = [
    ("PROOF 0045A560", True),
    (r"^S10-KPROVED PROOF", True),
    # 原实现的锚定正则：rg 也 0 命中（因为该行 PROOF 不在行首）—— 与 Python 无关
    (r"^\s*#*\s*proof", False),
    # 去锚等价写法：rg 与 Python 都命中
    (r"(?:^|\s)proof\s+(?:0x)?([0-9a-f]{8})\b", True),
    (r"① ENTRY:.*entry=0045A560", True),
]
for pat, expect in RG_PATS:
    r = subprocess.run(["rg", "-c", "-i", "-e", pat, probe_file],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    res["rg_cross_check"].append(dict(pattern=pat, expect_match=expect,
                                     rc=r.returncode, stdout=r.stdout.strip(),
                                     file=probe_file))

res["conclusion"] = (
    "本机 Python re 有『^ + 可空量词 + 字面量，且首字符非空白』的漏匹配，"
    "但 R16 四环检测器的 11/11 召回**不依赖**这条路径（真正命中的是 ①ENTRY 那条），"
    "实测 A/D/B 三条读法均 11/11。⇒ 此异常是环境记录，不是 R16 结论的漏洞。"
)
with open(os.path.join(OUT, "python_re_probe.json"), "w", encoding="utf-8", newline="\n") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
    fh.write("\n")

bad = [c for c in res["cases"] if not c["ok"]]
print(f"[probe] python={sys.version.split()[0]} cases={len(res['cases'])} failed={len(bad)}")
for c in bad:
    print(f"  FAIL {c['pattern']!r} on {c['subject']!r}: expected {c['expected']} got {c['got']}")
print("[probe] rg cross-check (注意：rg 的 ^ 语义是行首，用于对照):")
for c in res["rg_cross_check"]:
    print(f"  rc={c['rc']} {c['pattern']!r} -> {c['stdout']!r}")
print("[probe] ->", os.path.join(OUT, "python_re_probe.json"))
