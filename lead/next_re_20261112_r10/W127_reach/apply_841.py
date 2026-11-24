#!/usr/bin/env python3
"""Append §841: ②-b data layer landed -- correct overlap detector + builder patch."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §841 · **②-b 数据层落地：恒真的重叠断言已修好；NAPOWR=3×2 得到独立佐证，"10 格重叠"首次被工具验证**（2026-11-15 18:20）

- **§841-1 [已证·原缺陷（§630-3 点名但未修的整改项）]**
  `w94_build.py:overlap_cells()` 对**所有建筑硬编码 2×2** footprint：
  ```python
  def overlap_cells(cells):
      # 2x2 footprint check: (r,c) covers rows r..r+1, cols c..c+1
      for rr in (r, r+1):
          for cc in (c, c+1): ...
  ```
  - NAPOWR 的真实 footprint 是 **3×2**（见 §841-3）。列距 2 时：
    - 真实 3 宽跨度 = `46-48, 48-50, 50-52, 52-54, 54-56, 56-58` ⇒ **相邻互相重叠**；
    - 2×2 模型跨度 = `46-47, 48-49, 50-51, ...` ⇒ **互不重叠**。
  - ⇒ `assert overlap_cells(nap) is None` 对 step2 与 step3 **都返回 None**（**已实测确认**，见 §841-2 第 3 项）
    ⇒ **该断言从未检查过任何东西**。这正是 §630-3 说的"空检查"，且"10 格"是手算、从未被工具验过。

- **§841-2 [已证·修正后的实测（`W129_overlap\verify_build_patch.py` → PASS）]**
  | 检查 | 结果 |
  |---|---|
  | 打过补丁的 `w94_build.py` 能正常 import（语法 OK） | OK |
  | 新函数 `overlap_cell_count_fp(step2, 3, 2)` | **10 格** |
  | 新函数 `overlap_cell_count_fp(step3, 3, 2)` | **0 格** |
  | 旧 `overlap_cells(step2)` / `(step3)` | **都返回 None** ⇒ 证实旧断言恒真 |
  | 新 `overlap_cells_fp(step2)` | 命中 `(56,48)` ⇒ 真的有碰撞 |
  | 模块内两条断言对 step2 / step3 分别试跑 | **都 PASS** |
  - **step2 的 10 个碰撞格**：`(56,48),(56,50),(56,52),(56,54),(56,56)` 与
    `(57,48),(57,50),(57,52),(57,54),(57,56)` ⇒ **5 个共享列 × 2 行 = 10**，
    与 §630-3 的手算值**精确一致**。

- **§841-3 [已证·NAPOWR = 3×2 的三重依据]**
  1. **真机测量**：§669 记录"16 格 = 4×4，**6 格 = 3×2**"，而 NAPOWR 是实验中唯一改变间距的建筑，6 格即 3×2。
  2. **算术反证**：只有宽度 3 才能让 step2 的相邻跨度共享 1 列、从而给出 **10 格**；若宽度为 2 则给出 **0 格**
     （§841-2 已实测）⇒ **footprint=3×2 是唯一与"10 格"自洽的取值**。这是一个可证伪检验，不是假设。
  3. **结构佐证**：§681-4 已证 footprint 是"按类型的静态常量表"，与"NAPOWR 恒为 3×2"相容。
  - ⚠️ **仍未做**：从 `artmd.ini` 直接读 `Foundation=` 交叉确认（项目内无抽出的 artmd.ini；MIX 提取路径未打通，见 §630-3）。

- **§841-4 [已证·改动清单（最小、可回退）]**
  | 位置 | 改动 |
  |---|---|
  | `w94_build.py:overlap_cells` | **行为不变**（仍是 2×2），但加了醒目注释说明它对非 2×2 建筑是错的、且曾使断言空转；改为委托 `overlap_cells_fp(cells,2,2)` |
  | `w94_build.py:overlap_cells_fp(cells,w,h)` | **新增**：任意 footprint 的碰撞检测 |
  | `w94_build.py:overlap_cell_count_fp(cells,w,h)` | **新增**：返回被 >1 栋覆盖的格数 |
  | `w94_build.py:NAPOWR_FP = (3,2)` | **新增**：实测 footprint 常量 |
  | 设计生成处（原 283-286 行） | 改用 footprint 感知检测；把真实格数写进 design JSON 的 `napowr_overlap_cells`；新增断言"重叠数是否为零 ⟺ 是否为 step3 臂" |
  | 事后自检处（原 413-415 行） | 同上；step3 断言**重叠数必须为 0**，step2 断言**必须 >0** |
  - ⇒ 新旧断言对现有两种臂**行为一致**（step3 通过、step2 通过），但**从"恒真"变成"真检查"**：
    若将来有人把 step3 的坐标改成会重叠，现在会**真的失败**。

- **§841-5 [已证·对 ②-b 修复结论的影响]**
  - 数据层"禁止多格建筑重叠"**现在是可执行、可验证的**：`W129_overlap\overlap_check.py` 可对任意
    `structures` 列表（design JSON）做 fail-closed 检查（未知类型直接报错，绝不猜）。
  - 但按 §837，**它只覆盖成因 A**；成因 B 仍是未证推测。本步不改变该结论。
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §841" in src:
    sys.exit("ABORT: §841 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §841", "10 格", "NAPOWR_FP"):
    print("  %-12s %d" % (k, back.count(k)))
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
