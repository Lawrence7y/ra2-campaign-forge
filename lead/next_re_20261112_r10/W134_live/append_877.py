#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append §877: correcting §862's function identity; the conclusion survives and strengthens."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
s = io.open(LED, encoding="utf-8", newline="").read()

SEC = """
## §877 · **【更正 §862】真正的 `AbstractClass` 构造器是 `0x00410170`（44 调用者），不是 `0x004101F0` —— 但"根类不登记"的结论由全部 5 个函数共同支持，反而更强**（2026-11-15 17:40）

> 来源：`ds-t3-registry` 的收尾报告 + **我对全部 5 个函数逐条反汇编**。
> 性质：**更正 §862 的函数身份**；结论不变且证据面从 1 个扩到 5 个。

- **§877-1 [已证·5 个安装 `AbstractClass` 四虚表的函数，逐个实测]**
  | 函数 | 大小 | 调用者 | 性质（我判定） | 函数体内 registry 引用 |
  |---|---:|---:|---|---:|
  | **`0x00410170`** | 71 | **44** | **真·构造器**：初始化 `+0x08`/`+0x0C`（次级虚表）、`+0x18=0`、`+0x1C=0`、`+0x20=0`、`+0x14` 标志位、`+0x10=-1`，并装 4 个主虚表 | **0** |
  | `0x004101C0` | 46 | 27 | 构造变体（`ret 4`，装 4 主虚表 + 2 次级） | **0** |
  | `0x004101F0` | 28 | 31 | **仅装 4 个主虚表**后 `ret`（无字段初始化） | **0** |
  | `0x004105A0` | 53 | 0 | **标量删除析构器**：`test al,1` → `call 0x7C8B3D`（`operator delete`）→ `ret 4` | **0** |
  | `0x006E8000` | — | — | 不在函数图谱内（未建函数），**未验** | — |
  - ⇒ **5 个（4 个已验 + 1 个未验）全部 0 引用 `0xB0F720/24/28/2C/30/34`。**

- **§877-2 [已证·§862 错在哪]**
  §862 把 **`0x004101F0`** 称作"`AbstractClass` 的构造器"。**这个身份不对**：
  - `0x004101F0` 只有 4 条 `mov [ecx+k], vtable` + `ret`，**没有任何字段初始化**；
  - 真正做字段初始化的是 **`0x00410170`**（71 字节、44 个调用者，`+0x10=-1`、`+0x18`、`+0x1C`、`+0x20`、`+0x14` 位操作）。
  - ⇒ 更准确的描述：`0x00410170` = 构造器；`0x004101C0`/`0x004101F0` = **只装虚表的辅助函数**（供不需要完整初始化的派生路径复用）；`0x004105A0` = 标量删除析构器。

- **§877-3 [已证·结论不变，且证据更强]**
  §862 的结论是"根类构造器不登记 ⇒ 注册表完整性不能由根类保证"。
  - **该结论成立**，而且现在由 **4 个已验函数全部 0 引用**共同支持，
    不再依赖"我把哪一个函数认成构造器"这个判断。
  - ⇒ **即使我认错了函数，结论也不受影响** —— 这正是我该给的证据形式（穷举该类的全部 vtable 安装点），
    而不是依赖单点识别。
  - ⇒ 与 **§868**（`FootClass` 构造器登记自己的表、对 `0xB0F720` 0 引用）、
    **§867/§874**（`AbstractClass*` 有 12 个数组）三条独立证据**同向**。

- **§877-4 [已证·登记点的完整清单（子代理给出，我照录未逐条复验）]**
  AddItem 站点形态为 `inc ecx` → `mov [0xB0F730], ecx`（字节 `89 0D 30 F7 B0 00`）：
  | 类 | 函数 | 站点 |
  |---|---|---|
  | `ObjectClass` | `0x005F3900` | `0x005F3A7F` |
  | `AlphaShapeClass` | `0x00420960`、`0x00420AF0` | `0x00420A62`、`0x00420BBF` |
  | `FactoryClass` | `0x004C98B0` | `0x004C99EC` |
  | `HouseClass` | `0x004F54A0` | `0x004F5FF5` |
  | `ParticleSystemClass` | `0x0062DC50`、`0x0062DF20` | `0x0062DEF6`、`0x0062E05B` |
  | `TeamClass` | `0x006E8A90` | `0x006E8C87` |
  - ⇒ 归因到 **8 个不同类 / 6 个构造函数体**。
  - ⇒ `BuildingClass`、`UnitClass`、`InfantryClass`、`AircraftClass`、`TechnoClass`、`FootClass`、
    `BulletClass`、`AnimClass`、`OverlayClass`、`TerrainClass`、`SmudgeClass`、`HouseClass`(构造)
    **均不在 AddItem 清单里** ⇒ 与 §868 一致。

- **§877-5 [已证·子代理两次否掉我给它的启发式]**
  我传给它的"1 次 `Items` + 3 次 `Count` = push"这条启发式，**它两次证明是错的**：
  | 函数 | 我的启发式判 | 实际 |
  |---|---|---|
  | `0x005F3B80` | push | **析构函数**（pop） |
  | `0x007258D0` | push | **根本不改 `Count`**；它遍历数组并对每个元素调槽 `+0x28`（死亡广播） |
  - ⇒ 与 **§875-1** 同源：**"形状像"不等于"是"**。方向必须由 `inc`/`dec` 定，不能由"引用了几次"定。
  - ⇒ 这是我在本轮第 **4** 次栽在同一类错误上（T1 的 20 dwords、守卫判定、`table` 评级、这条启发式）。

- **§877-6 [未证·如实登记]**
  1. `0x006E8000` **不在函数图谱内**（Ghidra 未建函数），我未反汇编它，因此"5 个全部 0 引用"实际是"**4/5 已验**"。
  2. AddItem 站点清单（§877-4）**我未逐条复验**，只照录。
  3. **未枚举每个叶子构造器**确认它是否内联 `AddItem` —— 这是把"可证明不完整"升级为完整普查的唯一测量，未做。
  4. `0x00421730`（AlphaShapeClass 构造器却执行 `RemoveItem`）**只能经 vtable 槽到达**（0 个直接 `call` 者），
     哪个调用点到达它**未知**；因此它作为"反例"的强度受限于"该路径是否真的可达"。
  5. 12 个 `AbstractClass*` 数组**各自收什么类、是否互不相交**，完全未知。
  6. `0xB0F720` 在 BSS 尾部，运行时内容不可静态观测——只有写它的代码可观察。
"""

if "## §877 ·" in s:
    raise SystemExit("REFUSE: §877 already present")

OLD = ("  - `function_atlas.tsv`：`entry=0x004101f0 size=28 n_instr=5 n_callers=31 n_callees=0`，\n"
       "    下一个函数从 `0x00410210` 开始 ⇒ **函数体就是这 28 字节，后面没有藏着登记代码**。")
NEW = ("  - `function_atlas.tsv`：`entry=0x004101f0 size=28 n_instr=5 n_callers=31 n_callees=0`，\n"
       "    下一个函数从 `0x00410210` 开始 ⇒ **函数体就是这 28 字节，后面没有藏着登记代码**。\n"
       "  - ⚠️ **但 `0x004101F0` 不是真正的构造器**（§877 更正）：它只装虚表、不做字段初始化。\n"
       "    真构造器是 **`0x00410170`**（71 字节、44 调用者、初始化 `+0x10=-1` 等），**同样 0 引用注册表**。\n"
       "    该类的 **4 个已验 vtable 安装点全部 0 引用** ⇒ 结论不变且更强。")
if s.count(OLD) == 1:
    s = s.replace(OLD, NEW)
    print("§862 forward pointer added")
else:
    print("WARN: §862 anchor found %d times, skipped" % s.count(OLD))

s = s.rstrip("\n") + "\n" + SEC
io.open(LED, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("appended §877; size=%d; control chars=%d" % (len(s.encode("utf-8")), len(bad)))
