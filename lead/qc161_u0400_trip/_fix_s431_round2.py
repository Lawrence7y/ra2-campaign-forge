#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§431 二次就地更正（提交前自查抓出的三处，字节锚定）。

自查教训（登记用）：更正 1 本身又引入一处口径错（泵体即 ret ⇒「不占 CPU」——
忽略了外层 cmp/je 回环立刻再 call）；esi 装载点地址凭 v1 错位窗口记成「0x6BD76E
邻域」，v4 原始字节实为 0x6BD7C5。⇒「对『修正』本身也要跑负控」。
"""
import io, os

LEDGER = "lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
data = io.open(LEDGER, "rb").read()

# --- 更正 A：esi 装载点地址 + 块区起点措辞 + 泵自旋语义 ---
OLDA = ("- 块区起点 0x6BD7C7，每 ~0x3D 字节一块、共 ≥33 块；序言区 0x6BD7xx 有\r\n"
        "  `mov esi,[0x81C1D0]`（0x6BD76E 邻域实测）⇒ **`call esi` 的 callee = 全局函数指针\r\n"
        "  [0x81C1D0]，全镜像仅 2 个写者**：").encode("utf-8")
NEWA = ("- 块区自 ~0x6BD7C7..0x6BD7D0 起、每 ~0x3D 字节一块、≥33 块（v1 解码窗起点，\r\n"
        "  精确头对齐留待断点趟）；窗首实测 `mov esi,[0x81C1D0]` @0x6BD7C5\r\n"
        "  （原始字节 8B 35 D0 C1 81 00，v4 hexdump 钉死）⇒ **`call esi` 的 callee = 全局\r\n"
        "  函数指针 [0x81C1D0]，全镜像仅 2 个写者**：").encode("utf-8")
assert data.count(OLDA) == 1, "anchorA miss"
d2 = data.replace(OLDA, NEWA)

OLDB = ("  泵体头三条：`mov eax,[0xB73550]; test eax,eax; je 0x5D4E66` ⇒ **hwnd==0 时泵体首分支\r\n"
        "  即 pop×4/add esp/ret**（0x5D4E66 本轮补解码实测）——不空转、不占 CPU，纯等。\r\n").encode("utf-8")
NEWB = ("  泵体头三条：`mov eax,[0xB73550]; test eax,eax; je 0x5D4E66`；0x5D4E66=pop×4/add esp/\r\n"
        "  ret（本轮补解码实测）⇒ **hwnd==0 时泵体本身不干活即 ret**；但外层 `je 0x6BE0DC`\r\n"
        "  立刻再 call ⇒ **主线程紧自旋（CPU 占满），等 exitstate≠1**——与 §429「150 s\r\n"
        "  不退+ws 爬升」现场一致（自旋解释存活，「泵体空转」与「不占 CPU」两措辞均废）。\r\n").encode("utf-8")
assert d2.count(OLDB) == 1, "anchorB miss"
d3 = d2.replace(OLDB, NEWB)

# --- 更正 C：§三 末三行——无守卫分歧位置（不是块本身/不是 vtable call，是块下游消费链） ---
OLDC = ("⇒ exitstate 永停 1 ⇒ 静默僵尸。[推断] 无守卫现场同一位置走\r\n"
        "`mov ecx,[0x887368]; call [ecx 的 vtable]` 族 → null 解引用 → AV（RC-4 本体）；\r\n"
        "两臂同源，闸门同一点：修复的「视为完成」= 停机态让 1→2 照常发生（见四 c′）。\r\n").encode("utf-8")
NEWC = ("两臂在「清零块之后」分歧：无守卫臂的退出链消费者（0x652CF0→v[42]→0x724730 族，\r\n"
        "§398 已闭合链）解引用 null→AV＝RC-4；守卫臂同一批消费调用被拦返 0⇒链走完闩 1，\r\n"
        "却等不来 bump。闸门同一点：修复的「视为完成」= 停机态让 1→2 照常发生（见四 c′）。\r\n").encode("utf-8")
assert d3.count(OLDC) == 1, "anchorC miss"
d4 = d3.replace(OLDC, NEWC)

# 措辞收尾：§三 第一句里的 [推断] 句已被 C 更正吸收，检查残留
assert "[推断] 无守卫现场同一位置走" not in d4.decode("utf-8"), "stale inference line remains"

assert b"\xc2\xa7430" in d4 and b"\xc2\xa7431" in d4
tmp = LEDGER + ".tmp431fix2"
io.open(tmp, "wb").write(d4)
os.replace(tmp, LEDGER)
back = io.open(LEDGER, "rb").read()
assert back == d4
print("OK 三处更正落位; ledger %d bytes crlf=%d" % (len(back), back.count(b"\r\n")))
