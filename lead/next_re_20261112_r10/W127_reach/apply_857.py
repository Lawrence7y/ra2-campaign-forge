#!/usr/bin/env python3
"""Append §857: final consistency audit + goal completion evidence."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §857 · **收口审计：五个里程碑的产物互相一致（OVERALL PASS），目标达成**（2026-11-16 08:00）

- **§857-1 [已证·审计方法]** `W131_subsystems\final_audit.py`：不是"看文件在不在"，
  而是**核对跨文件计数是否互相自洽**（同一量在不同产物里的数值必须相等，且集合能对上）。

- **§857-2 [已证·审计结果（OVERALL: PASS）]**
  | 组 | 检查项 | 结果 |
  |---|---|---|
  | 里程碑1 | `class_atlas_v2` 类数 = **988** | OK |
  | | 其中 有虚表 **954** / 纯接口 **34** | OK |
  | | `vtables_canonical` 虚表 **1,214** / 主表 **954** / 涉及类 **954** | OK |
  | 里程碑2 | `function_atlas` 行数 = **12,916** | OK |
  | | 代码字节 = **3,225,845**；`.text` 覆盖 **79.5%** | OK |
  | | 函数指针条目 = **6,303** | OK |
  | 里程碑3 | `fn_subsystem_canonical` 行数 = **12,916** | OK |
  | | **集合与函数图谱完全一致**（无重复、无遗漏） | OK |
  | | 已归类 **5,497** / 字节 **2,091,344** / 子系统 **26** 个 | OK |
  | 里程碑4 | `field_layout_classes` 338 行 / `field_layout_subsystems` 2,532 行 | OK |
  | | `FIELD_LAYOUT.md` 存在且 >8 KB | OK |
  | | `vtable_members` 13,351 行 / `fn_class` 6,256 行 | OK |
  | 里程碑5 | 台账含 §846–§856 全部 11 节 | OK |
  | | 台账 **[已证] 标记 1,077 处 / [未证] 283 处** | OK |
  | | 13 个可复跑脚本全部在位 | OK |

- **§857-3 [已证·五个里程碑的最终交付物]**
  | # | 里程碑 | 交付物 | 关键数字 |
  |---|---|---|---|
  | 1 | 全量类图谱 | `W130_atlas\class_atlas_v2.tsv/.json`、`vtables_canonical.json` | **988 类**（954 有虚表 + 34 纯接口）/ 1,214 虚表 / 954 主表 |
  | 2 | 全量函数图谱 | `W130_atlas\function_atlas.tsv` | **12,916 函数** / 3,225,845 B / 79.5% `.text` |
  | 3 | 子系统地图 | `W131_subsystems\fn_subsystem_canonical.tsv`、`subsystems_canonical.tsv` | **26 子系统** / 42.6% 函数 / 64.8% 字节，带 T1/T2 分层 |
  | 4 | 子系统入口与结构 | `FIELD_LAYOUT.md`、`field_layout_*.tsv`、`subsystem_structure.json` | **7 个入口**（含主循环/初始化）+ **11 类 / 23 子系统**的结构条目 |
  | 5 | 脚本与分级 | 13 个 `.py` + 5 个 `.java` | 台账 [已证] 1,077 / [未证] 283 |

- **§857-4 [已证·交付过程中被推翻/修正的旧结论（诚实清单）]**
  | 旧结论 | 修正 | 节 |
  |---|---|---|
  | 继承 RTTI 表 1,305 个虚表可信 | **87 个 `.text` 假阳性 + 1 `.rsrc` + 5 `.data` + 9 截断名** ⇒ canonical **1,214** | §846/§848/§849 |
  | 类总数 962 | **988**（954 + 34 接口） | §849-2/§850 |
  | `+0x2C` = WhatAmI 是普遍规律 | **只在 `ObjectClass` 树成立**；真值 144，不是 185 | §846-7/§848-4 |
  | 函数总数 8,948（可枚举 8,578） | **管理器 13,286 / 可枚举 12,916** —— 旧图谱漏 1/3 代码 | **§851** |
  | 子表槽数 ≤ 主表槽数 | **被否证**：`LocomotionClass` 子表 49 槽 > 主表 10 槽 | §849-4 |
  | GLM 子系统图覆盖率 78.8% | **不可采信**：含 2,615 通用容器误标 + AUDIO 12 倍虚高 ⇒ canonical 42.6% | §854 |
  | `EIP=0` 是项目内最多崩溃签名 | **错**：真机现场 25/26 是 ②-a | §835 |

- **§857-5 [未证·如实登记的剩余缺口]**
  1. **20.5% 的 `.text` 字节**仍不属于任何已建函数（对齐填充 / `.text` 内数据 / 未被发现的函数）。
  2. **57.4% 的函数**没有证据支撑的子系统归属（调用图对虚方法无效）。
  3. `field_layout` 尚未按 `param_1` 真实类型分桶、未做继承链归并、未区分数组索引访问。
  4. WhatAmI 只覆盖 144 个 `ObjectClass` 系类（其它类无该方法，属事实）。
  5. 那 370 个"计入总数但不可枚举"的函数条目仍未解释。
  6. §853 找到的 `DAT_00a8eb44`（疑似单位主表）**未真机验证**。
  - ⇒ 这 6 条都不阻塞里程碑的"可判定完成度"，但都影响后续深度。
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §857" in src:
    sys.exit("ABORT: §857 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §857", "OVERALL", "1,214"):
    print("  %-12s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
