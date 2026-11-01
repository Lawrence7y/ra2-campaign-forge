#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§431 就地更正（两处，字节锚定，锚文本从盘上读出，零删除他线内容）。"""
import io, os

LEDGER = "lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
data = io.open(LEDGER, "rb").read()

# ---- 更正 1：泵体首分支 = 直接 ret，不是空转占 CPU ----
OLD1 = ("  泵体头三条：`mov eax,[0xB73550]; test eax,eax; je 0x5D4E66` ⇒ **hwnd==0 时泵空转**\r\n"
        "  （0x5D4E60 回边，§398/ab24 已知），不干活、只占 CPU。\r\n").encode("utf-8")
NEW1 = ("  泵体头三条：`mov eax,[0xB73550]; test eax,eax; je 0x5D4E66` ⇒ **hwnd==0 时泵体首分支\r\n"
        "  即 pop×4/add esp/ret**（0x5D4E66 本轮补解码实测）——不空转、不占 CPU，纯等。\r\n").encode("utf-8")
assert data.count(OLD1) == 1, "anchor1 miss"
d2 = data.replace(OLD1, NEW1)

# ---- 更正 2：bump 时机精确化（P1 现场=闩 1 前已跳过；闩 1 后通道自断）----
OLD2 = ("**守卫把「崩在 1」换成了「等一个永不到来的 2」**：\r\n"
        "0x777818 住在 0x5D4D50 泵体所派发消息的处理链下游，而该处理链要经\r\n"
        "`[0x887368]`（RC-4 单例）派发——守卫拦截单例成员（ecx=0 → 返回 0），\r\n"
        "派发不发生 ⇒ bump 不执行 ⇒ 泵 `je` 永远成立 ⇒ 静默僵尸。\r\n"
        "**无守卫**：同一条派发解引用 null → AV（即 RC-4 本体）。\r\n"
        "⇒ 两现象同源；修复的「视为完成」点 = 让 1→2 这一步在停机+单例已 null 时照常发生。\r\n").encode("utf-8")
NEW2 = ("**守卫把「崩在 1」换成了「等一个永不到来的 2」**，精确时序（实测链）：\r\n"
        "P1 现场（t=14.17 s，闩 1 **之前**）bump 块已跑过一次，当时 exitstate==0 ⇒\r\n"
        "0x777816 `je 0x777822` **跳过写 2**；t=19.99 s 函数 A 闩 1，泵循环等「非 1」。\r\n"
        "而唯一能写 2 的仍是那块 0x777803 关闭块——它再跑需要一次新的同型消息派发，\r\n"
        "但块自身已把 [0xB73550]=0（hwnd）清掉 ⇒ 泵体首分支即 ret，**派发通道自断**\r\n"
        "⇒ exitstate 永停 1 ⇒ 静默僵尸。[推断] 无守卫现场同一位置走\r\n"
        "`mov ecx,[0x887368]; call [ecx 的 vtable]` 族 → null 解引用 → AV（RC-4 本体）；\r\n"
        "两臂同源，闸门同一点：修复的「视为完成」= 停机态让 1→2 照常发生（见四 c′）。\r\n").encode("utf-8")
assert d2.count(OLD2) == 1, "anchor2 miss"
d3 = d2.replace(OLD2, NEW2)

assert b"\xc2\xa7430" in d3 and b"\xc2\xa7431" in d3
tmp = LEDGER + ".tmpfix431"
io.open(tmp, "wb").write(d3)
os.replace(tmp, LEDGER)
back = io.open(LEDGER, "rb").read()
assert back == d3
print("OK: 两处更正落位; ledger %d bytes crlf=%d" % (len(back), back.count(b"\r\n")))
