#!/usr/bin/env python3
"""Append §850: class atlas v2 artifact + milestone-1 closure."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §850 · **里程碑(1) 收口：类图谱 v2 产出 `class_atlas_v2.tsv/.json`（988 类 = 954 有虚表 + 34 纯接口）**（2026-11-16 01:00）

- **§850-1 [已证·最终数字（三处独立来源一致）]**
  | 量 | 值 | 来源 |
  |---|---:|---|
  | 结构完整 TypeDescriptor | **988** | 我（本节脚本）；GLM 独立扫描同样得 988 |
  | 有虚表实现的类 | **954** | 我的 canonical 集（1,214 虚表） |
  | 纯接口类（有 TD、无本地虚表） | **34** | 同上 |
  | 虚表 | **1,214** | 我方重建 + DeepSeek 严格 + GLM 抽查 三方收敛 |
  | 主虚表（`COL.offset==0`） | **954** | 每类恰好一张（I1 不变量通过） |

- **§850-2 [已证·34 个纯接口类全部是 COM/ATL 接口，与"无本地虚表实现"自洽]**
  实测清单（`.?AU` 前缀 = struct/interface）：
  `IApplication`、`IClassFactory`、`IConnectionPoint`、`IConnectionPointContainer`、
  `IEnumConnectionPoints`、`IEnumConnections`、`IPersist`、`IPersistStream`、
  `ISequentialStream`、`IStream`、`IUnknown`、`IRTTITypeInfo`、`IPiggyback`、
  `IUIHouse`/`IUIPublicHouse`/`IUIGameMap`/`IUILocomotion`/`IUIFlyControl`/`IUISwizzle`/`IUILinkStream`、
  WOL 事件族（`IChatEvent@WOL`、`IDownloadEvent@WOL`、`INetUtilEvent@WOL`、`IWOLBrowserEvent`），
  以及 ATL 的 `CComObjectRootBase`/`?$CComObjectRootEx@VCComMultiThreadModel@ATL@@@ATL@@`
  与少量模板/工具类型（`?$Node@PAUINIEntry@INIClass@@`、`?$Node@PAVMixFileClass@@`、
  `?$DynamicVectorClass@W4DiskID@@@@`、`BounceClass`）。
  - ⇒ **"有 TD 无虚表"的解释成立**：这些是**只被 `QueryInterface` 暴露的纯接口**（或被内联/未发射的模板），
    它们在引擎里没有独立的虚表实例，符合 COM 用法。
  - ⚠️ 仍未排除另一种可能：其实现表存在但不在我的扫描范围内（`.rdata/.data` 的 raw 区）。见 §849-6.2。

- **§850-3 [已证·产物]** `W130_atlas\`
  | 文件 | 内容 |
  |---|---|
  | **`class_atlas_v2.tsv` / `.json`** | **权威类图谱**：class / kind(class_with_vtable | interface_only) / n_vtables / primary / primary_slots / max_sub_slots / vtables |
  | `vtables_canonical.json` | 1,214 条虚表（vt/col/class/sig/col_offset/section） |
  | `vtables_v2.json` | 同上 + v2 槽计数与终止原因 |
  | `function_atlas.tsv` | 8,578 函数（含字符串、导入、调用计数） |
  | `class_atlas_v2.py` / `atlas_v2.py` / `reconcile_vtables.py` | 可复跑生成器 |

- **§850-4 [已证·里程碑(1) 交付判定]** 目标里对里程碑(1) 的要求是
  "962 个 RTTI 类，每个含类名/所有虚表地址/虚表槽数/WhatAmI ID/主虚表判定"。
  | 要求项 | 状态 |
  |---|---|
  | 类名 | **988 个全覆盖**（原目标写 962，实测 988 —— 目标里的数字偏低，已在 §849-2 更正） |
  | 所有虚表地址 | **1,214 条全覆盖**（有实现的 954 类；34 接口为 0 张，属于事实而非缺失） |
  | 虚表槽数 | **v2 规则全覆盖**（78% 终止有结构解释，其余 22% 为 `data`/`other`，已标注原因） |
  | **WhatAmI ID** | **⚠️ 只能覆盖 144 个类**（仅 `ObjectClass` 树），其余类**该槽位不是 WhatAmI**（§848-4） |
  | 主虚表判定 | **954/954 全覆盖**（`COL.offset==0`，I1 不变量通过） |
  - ⇒ **结论：里程碑(1) 达成 4.5/5 项。"WhatAmI ID 全覆盖"这一项在物理上不成立** ——
    因为大多数类根本没有 WhatAmI 方法。**建议把该要求改写为"ObjectClass 继承树内的 WhatAmI 全覆盖（144/144）"**，
    该改写后的子目标**已达成**。
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §850" in src:
    sys.exit("ABORT: §850 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §850", "class_atlas_v2", "4.5/5"):
    print("  %-18s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
