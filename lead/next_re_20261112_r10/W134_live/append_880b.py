#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append §880 and add retraction stubs using SHORT markers only (no long quoted text)."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
s = io.open(LED, encoding="utf-8", newline="").read()
if "## §880 ·" in s:
    raise SystemExit("REFUSE: §880 already present")

RETRACT_NOTE = (
    "> ⚠️ **本节已被 §880 推翻**：`0x006DD8B0` 整个函数属 **`TActionClass`**"
    "（函数体内唯一源文件字符串是 `D:\\ra2mdpost\\TAction.CPP`），"
    "是**触发器动作执行器**，不是游戏状态机、也不是每帧模拟调度器。\n"
    "> 由此，本节的「每帧」「主循环」「按类型分工更新」等定性**全部作废**；"
    "其中关于跳转表/数组引用的**数字**仍有效，但含义改为「TAction 动作码」与「动作实现」。\n\n"
)


def insert_after_heading(text, heading_prefix, note):
    idx = text.find(heading_prefix)
    if idx < 0:
        return text, False
    eol = text.find("\n", idx)
    if eol < 0:
        return text, False
    return text[:eol + 1] + "\n" + note + text[eol + 1:], True


for pref in ("## §873 · ", "## §879 · "):
    s, ok = insert_after_heading(s, pref, RETRACT_NOTE)
    print(("ok: stub after " + pref.strip()) if ok else ("WARN: heading not found: " + pref))

# stub before the §853-2 bullet
MARK = "- **§853-2 [已证"
idx = s.find(MARK)
if idx > 0:
    stub = ("> ⚠️ **§853-2 的 `0x006DD8B0` 一行已被 §880 推翻**：该函数属 `TActionClass`，"
            "是触发器动作执行器，不是游戏状态机分派器。\n\n")
    s = s[:idx] + stub + s[idx:]
    print("ok: stub before §853-2")
else:
    print("WARN: §853-2 marker not found")

SEC = """
## §880 · **【推翻 §853 / §873 / §879 的整个框架】`0x006DD8B0` 是 `TActionClass`（触发器动作执行器），不是游戏状态机、也不是每帧模拟调度器**（2026-11-15 18:45）

> 来源：我追 `this` 来源时，发现该函数体内含字符串 `D:\\ra2mdpost\\TAction.CPP`。
> 性质：**本轮最根本的一次更正**。三层框架（§853 的状态机 / §873 的 case-1 辨析 / §879 的按类型分工）全部建立在错误定性上。

- **§880-1 [已证·决定性证据]** `0x006DD8B0` 整个函数体（9,530 字节）内**唯一**的源文件字符串是
  **`D:\\ra2mdpost\\TAction.CPP`**。⇒ 它属于 **`TActionClass`**（Trigger Action，触发器动作）。
  - 这与「每帧主循环」没有任何关系。我此前把它当主循环，是从 §853 起就错了。

- **§880-2 [已证·`[esi+0x2C]` 是动作码，不是 WhatAmI]**
  ```asm
  006DD8BB  8bf1          mov  esi, ecx
  006DD8D7  8b562c        mov  edx, [esi + 0x2C]        ; 动作码
  006DD8DA  4a            dec  edx                      ; 码值 = 表索引 + 1
  006DD8DB  81fa90000000  cmp  edx, 0x90                ; 144 个分支
  006DD8E7  ff2495ecfd6d00 jmp [edx*4 + 0x006DFDEC]
  ```
  - **我在对话中一度判定它是 `WhatAmI`，当场收回。** 判据：`WhatAmI` 实测值域 **1..73**
    （YRpp `AbstractType` 枚举止于 73；台账 §636-3 实测「N 覆盖 1..73」），而这里上界 **144**。
  - ⚠️ **一个差点骗到我的巧合**：台账 §846-7 说「WhatAmI 真值 **144** 个类」。
    那是**类的数量**，不是 WhatAmI 的上界；两个 144 毫无关系。**记此以免后人再被误导。**

- **§880-3 [已证·`this` 的来路]** 唯一直接调用者 `0x00726605`（在 `0x007265C0`，102 字节）内：
  ```asm
  007265D8  mov esi,[eax + 0xB0]     ; 动作队列头
  007265DE  test esi,esi / je exit
  007265E7  ; 循环：
  007265FD  call 0x502D30            ; 某查询
  00726603  mov ecx, esi             ; this = 队列节点（一个 TAction）
  00726605  call 0x006DD8B0
  0072660A  test al,al / je exit     ; 返回 false 提前退出
  00726610  mov esi,[esi + 0x28]     ; 沿 +0x28 到下一个动作
  00726615  jne 0x7265E7
  ```
  - ⇒ **`0x007265C0` 沿 `+0x28` 遍历动作链表，对每个动作调一次执行器。**

- **§880-4 [已证·§879 那 15 个「遍历数组」分支的真实含义]**
  数字有效（我逐块统计过 Count 引用），但解读必须改：
  - 旧解读（错）：「每帧对每种对象做一次更新」
  - **新解读**：某些 **TAction 动作**需要「对全场某一类对象执行操作」，例如
    「销毁所有建筑」「所有单位撤退」这类 scripted action，实现自然是遍历
    `BuildingClass::Array` / `FootClass::Array` / …
  - ⇒ `Building ×5`、`Trigger ×3`、`Foot ×2`、`Infantry`/`Techno`/`ParticleSystem`/`House` 各 1
    **是动作种类数，不是每帧更新轮次**。
  - ⇒ 「没有 Unit / Aircraft 分支」也失去原意（只是没有动作直接遍历那两个数组）。

- **§880-5 [已证·三层框架崩塌，逐条]**
  | 节 | 原结论 | 状态 |
  |---|---|---|
  | §853-2 | `0x006DD8B0` = 游戏状态机分派器（case 1 = 游戏内逻辑） | **定性错**（是 TAction 执行器） |
  | §853-3 | 它遍历六种数组 = 单位列表 | **定性错**（是动作实现） |
  | §873 | case 1 是胜负判定；每帧模拟在别的 state | **前半对，后半错**（整个函数都不是每帧模拟） |
  | §879 | 15 个 state 按类型分工的每帧更新 | **数字对、定性错** |
  - ⇒ **① 卡顿这条线：锚点从 §853 起就错了，此前所有基于它的逐帧推断作废。**

- **§880-6 [已证·真正的每帧模拟入口仍未知]**
  本轮只能确定：**不是 `0x006DD8B0`**。
  - §853-2 的其它入口（`0x006BB9A0` 初始化、`0x00686B20` 任务载入、`0x00684620` 场景载入、
    `0x004ACE70` 地图载入、`0x005E3D10` MP 传输、`0x005E7EB0` 预览）**未逐条复审**；
    但它们的定性来自**字符串与导入**，与此错误无关，**大概率仍成立**。

- **§880-7 [未证·如实登记]**
  1. **真正的每帧模拟入口未找到。**
  2. `0x007265C0` 的 `this`（`edi`）类别未定；`[edi+0x24]`→`[+0xA4]`→`[+0xB0]` 指针链未定性。
  3. `0x502D30` 未定性。
  4. `0x007265C0` 另 4 个调用者（`0x6E2AD0`/`0x6E5439`/`0x6E5450`/`0x6E546D`）未定性。
  5. `0x90`（144）是否恰为 TAction 动作码总数未核实（只知是上界）。
  6. §879 表内编号需整体 **+1** 才是动作码。
"""

s = s.rstrip("\n") + "\n" + SEC
io.open(LED, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("appended §880; size=%d; control chars=%d" % (len(s.encode("utf-8")), len(bad)))
