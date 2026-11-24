#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Correct §863: the trap exists but NO consumer steps in it (verified)."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
s = io.open(LED, encoding="utf-8", newline="").read()

OLD = """- **§863-5 [已证·我的脚本在这一点上是对的]**
  我在本轮写的 `W132_arrays\\w132_array_globals.py` 与 `w132_series` 各脚本读该表用的是
  `int(p[1])`（十进制），**口径正确**；`entry` 用 `int(p[0], 16)`。因此
  §859 的 49 数组表与 §860 的 370 差额分析**不受此陷阱影响**。"""

NEW = """- **§863-5 [已证·没有任何消费者踩到这个坑（已逐个审计）]**
  我逐个检查了仓库中所有读取 `function_atlas.tsv` 的解析点，结论是**口径全部正确**：
  | 文件 | 解析写法 | 判定 |
  |---|---|---|
  | `W130_atlas\\clean_func_atlas.py:52` | `"entry": int(p[0], 16), "size": int(p[1])` | ✅ 正确（**同一 dict 里一个 hex 一个 dec，正是本陷阱最清晰的例证**） |
  | `W131_subsystems\\rebuild_atlas.py:43` | `smap[int(p[0], 16)] = (int(p[1]), ...)` | ✅ 正确 |
  | `W131_subsystems\\subsystem_structure.py:33` | `size[e] = int(p[1])` | ✅ 正确 |
  | `W131_subsystems\\emit_targets.py:18` | `int(p[1])` | ✅ 正确 |
  | `W132_arrays\\w132_array_globals.py`（本轮我写的） | `int(p[1])` | ✅ 正确 |
  - ⇒ **没有任何脚本把 size 当 hex 读**。因此台账已有的
    **79.5% `.text` 覆盖率**、**64.8% 字节覆盖率**、函数图谱字节数 **3,225,845 B**
    **全部不受影响，无需重算**。
  - ⇒ 本节记录的是**隐患**而非**已发生的错误**。措辞必须准确：**陷阱真实、后果严重（81% 越界），
    但本项目至今没有踩进去。**
  - ⇒ 唯一实测受影响的是**从未落地的第三方尝试**（子代理写的 `t4_textcov.py` 里出现过按 hex 的写法）。
    这也说明**代码审查该列一个检查项**：凡解析该表，`entry` 必须 `,16`，`size` 必须不 `,16`。"""

if s.count(OLD) != 1:
    raise SystemExit("REFUSE: §863-5 anchor found %d times" % s.count(OLD))
s = s.replace(OLD, NEW)
io.open(LED, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("§863-5 corrected; size=%d; control chars=%d" % (len(s.encode("utf-8")), len(bad)))
