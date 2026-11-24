#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append §862: AbstractClass has 4 vptrs and its ctor does NOT register."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

SEC = """
## §862 · **`AbstractClass` 是 4 基类多继承（4 个 vptr），且它的构造器完全不登记 —— §859 的"完整性可由根类保证"这条路断了**（2026-11-15 14:30）

> 来源：DeepSeek 子代理 `ds-t3-registry` 的转储，**由我独立复核**（虚表集合与 `col_offset` 双向对齐）。
> 纯静态，零真机。性质：**对 §859 不利**，推翻我自己在上面写的一条推理前提。

- **§862-1 [已证·事实]** `0x004101F0` 处函数完整内容 5 条指令 / **28 字节**：
  ```asm
  004101f0  mov dword ptr [ecx],   0x7e1f50      ; col_offset 0
  004101f6  mov dword ptr [ecx+4], 0x7e1f34      ; col_offset 4
  004101fd  mov dword ptr [ecx+8], 0x7e1f2c      ; col_offset 8
  00410204  mov dword ptr [ecx+0xc], 0x7e1f24    ; col_offset 12
  0041020b  ret
  ```
  - **它不碰 `0xB0F724`（Items）、不碰 `0xB0F730`（Count），`n_callees = 0`，因此也不可能间接登记。**
  - `function_atlas.tsv`：`entry=0x004101f0 size=28 n_instr=5 n_callers=31 n_callees=0`，
    下一个函数从 `0x00410210` 开始 ⇒ **函数体就是这 28 字节，后面没有藏着登记代码**。

- **§862-2 [已证·它确实是 `AbstractClass` 的构造器]** 双重对齐：
  | 源 | 内容 |
  |---|---|
  | `class_atlas_v2.tsv` 的 `.?AVAbstractClass@@` | 虚表 `0x7E1F24 / 0x7E1F2C / 0x7E1F34 / 0x7E1F50` |
  | `vtables_canonical.json` 的 `col_offset` | 分别 **12 / 8 / 4 / 0** |
  | `0x004101F0` 的 4 条 `mov` 目标 | `0x7E1F50 / 0x7E1F34 / 0x7E1F2C / 0x7E1F24` |
  ⇒ **四个虚表与四个 `col_offset` 一一对应**，不是巧合。

- **§862-3 [已证·推翻一条隐含假设：`AbstractClass` 有 4 个 vptr]**
  `AbstractClass` 是 **4 基类多继承**，vptr 在 **`+0 / +4 / +8 / +0xC`**。
  - §859 讲 `VectorClass` 布局时"vptr 在 `+0`"**对 `VectorClass` 成立**，
    但**不能外推**成"所有类只有一个 vptr 在 +0"。
  - ⇒ **警告下游**：凡"读 `[obj]` 即视为该对象的唯一虚表"的写法，对 `AbstractClass` 系对象只拿到
    **第一个基类**的虚表。`class_atlas_v2` 的数据本身没错（它记了 4 个），
    但任何假设"一类一虚表"的统计会漏掉另外 3 个子对象虚表。

- **§862-4 [已证·§859 的一条推理链断裂]**
  §859-6/§859-7-1 写的是："若登记发生在 `AbstractClass::AbstractClass`，则所有派生对象自动登记、数组即完整。"
  **前提被否证** —— 根类构造器只有 4 条 `mov` + `ret`。
  ⇒ 登记必然发生在别处，两种可能：
  - (a) 每个（叶子/中间）类的构造器各自内联 `AddItem` ⇒ **完整性必须逐类核对**；
  - (b) 存在专门的 `Add`/`Remove` 辅助函数，由**工厂/场景载入**调用 ⇒ 完整性取决于"是否所有创建路径都调了它"，**更难证**。
  - `n_callers = 31` 说明它被 31 个派生类构造器链式调用 —— 这正是"每类各自负责"的形态，
    而不是"根类统一兜底"。
  - ⇒ **口径收紧**：**`0xB0F730` 不可当作"对象总数"使用**，除非拿到逐类的正面证据。
    身份结论（`0xB0F720` 是 `DynamicVectorClass<AbstractClass*>`）**仍然成立**，不受影响。

- **§862-5 [已证·顺带：GLM 子代理本轮全线失败]**
  2026-11-15 13:23 派出的 6 个 GLM 子代理（T1..T6）到 14:30 **全部以"failed before it finished /
  no closing message"结束**，仅产出 4 个半成品文件。其中 `glm-t5-guards` 崩溃的**直接原因是一个
  格式串 bug**（`"E9 sites: %2d %s" % (t, len(...), ...)` —— 2 个占位符喂了 3 个参数），
  **不是分析困难**。
  - ⇒ 与 §861 合并看：先疑似限流（4 个连目录都没建），随后**全部失败**。
    本轮把 GLM 全部改派 DeepSeek（`magpie-anthropic/work/cn:deepseek-v4.1-flash`）重跑。
  - ⇒ 项目早前把"GLM 子代理零产出"归因为模型能力，**这个归因很可能是错的**（见 §861-2）。

- **§862-6 [已证·一条独立确认]**
  `glm-t5-guards` 崩溃前已算出：**`0x00724730` 的 `E8`（call rel32）调用点恰为 30 个**，
  地址全部列出（`0x4A8B75 … 0x6D1744`）。这与我声称的"30 个直接调用（28 未守卫 + 2 守卫）"
  **在总数上独立吻合**。守卫/未守卫的划分仍未复核（已改派 `ds-t5-guards`）。
"""

P = LED
s = io.open(P, encoding="utf-8", newline="").read()
if "## §862 ·" in s:
    raise SystemExit("REFUSE: §862 already present")
s = s.rstrip("\n") + "\n" + SEC
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("appended §862; size=%d bytes; control chars=%d" % (len(s.encode("utf-8")), len(bad)))
if bad:
    print("BAD:", bad[:5])
